#!/usr/bin/env python3
"""
Build first-cut txtrs-av runtime inputs directly from the local 2024 valuation PDF.

Current scope:
  - demographics/all_headcount.csv
  - demographics/all_salary.csv
  - demographics/entrant_profile.csv
  - demographics/salary_growth.csv
  - demographics/retiree_distribution.csv
  - decrements/reduction_gft.csv
  - decrements/reduction_others.csv
  - decrements/all_retirement_rates.csv
  - decrements/all_termination_rates.csv
  - funding/init_funding.csv

This script intentionally avoids using existing txtrs runtime files as inputs.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = PROJECT_ROOT / "prep" / "txtrs-av" / "sources" / "Texas TRS Valuation 2024.pdf"
OUT_DIR = PROJECT_ROOT / "plans" / "txtrs-av" / "data"

TABLE17_PDF_PAGE = 48
TABLE2_PDF_PAGE = 24
TABLE4_PDF_PAGE = 27
TABLE18_PDF_PAGE = 49
TERMINATION_PDF_PAGE = 68
RETIREMENT_PDF_PAGE = 69
SALARY_GROWTH_PDF_PAGE = 70
ENTRANT_PROFILE_PDF_PAGE = 76
REDUCTION_PDF_PAGE = 54

RUNTIME_RETIREE_MIN_AGE = 55
RUNTIME_RETIREE_MAX_AGE = 120

# AV Table 18 publishes 15 age bands. The runtime artifact starts at age 55, so
# the five pre-retirement bands ("Up to 35" through "55-59") are lumped into
# runtime ages 55-59. The published "100 & up" band fans out across the full
# runtime tail.
LIFE_ANNUITY_BAND_TO_RUNTIME: dict[str, tuple[int, int]] = {
    "Up to 35": (55, 59),
    "35-40": (55, 59),
    "40-44": (55, 59),
    "45-49": (55, 59),
    "50-54": (55, 59),
    "55-59": (55, 59),
    "60-64": (60, 64),
    "65-69": (65, 69),
    "70-74": (70, 74),
    "75-79": (75, 79),
    "80-84": (80, 84),
    "85-89": (85, 89),
    "90-94": (90, 94),
    "95-99": (95, 99),
    "100 & up": (100, RUNTIME_RETIREE_MAX_AGE),
}

LIFE_ANNUITY_TOTAL_COUNT = 475_891
LIFE_ANNUITY_TOTAL_ANNUAL = 13_100_519_264.0

AGE_MAP = {
    "Under 25": 22,
    "25-29": 27,
    "30-34": 32,
    "35-39": 37,
    "40-44": 42,
    "45-49": 47,
    "50-54": 52,
    "55-59": 57,
    "60-64": 62,
    "65 +": 67,
}

ENTRANT_AGE_BANDS = [
    "15-19",
    "20-24",
    "25-29",
    "30-34",
    "35-39",
    "40-44",
    "45-49",
    "50-54",
    "55-59",
    "60-64",
    "65-69",
]


def _pdf_page_text(pdf_path: Path, page: int) -> str:
    result = subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _extract_matching_line(lines: list[str], pattern: str) -> str:
    regex = re.compile(pattern)
    for line in lines:
        if regex.search(line):
            return line
    raise ValueError(f"Could not find line matching {pattern!r}")


def _strip_label(line: str, pattern: str) -> str:
    return re.sub(pattern, "", line, count=1)


def _extract_first_int_after_label(lines: list[str], pattern: str) -> int:
    line = _extract_matching_line(lines, pattern)
    payload = _strip_label(line, pattern)
    match = re.search(r"(\d[\d,]*)", payload)
    if not match:
        raise ValueError(f"Could not extract integer from line: {line}")
    return int(match.group(1).replace(",", ""))


def _extract_first_money_after_label(lines: list[str], pattern: str) -> float:
    line = _extract_matching_line(lines, pattern)
    payload = _strip_label(line, pattern)
    match = re.search(r"\$?\s*\(?([\d,]+(?:\.\d+)?)\)?", payload)
    if not match:
        raise ValueError(f"Could not extract money value from line: {line}")
    value = float(match.group(1).replace(",", ""))
    if "(" in payload and ")" in payload:
        value = -value
    return value


def _extract_first_percent_after_label(lines: list[str], pattern: str) -> float:
    line = _extract_matching_line(lines, pattern)
    payload = _strip_label(line, pattern)
    match = re.search(r"(\d+(?:\.\d+)?)%", payload)
    if not match:
        raise ValueError(f"Could not extract percent from line: {line}")
    return float(match.group(1)) / 100.0


def _parse_table17() -> tuple[pd.DataFrame, pd.DataFrame]:
    text = _pdf_page_text(PDF_PATH, TABLE17_PDF_PAGE)
    lines = text.splitlines()

    count_rows: list[dict] = []
    salary_rows: list[dict] = []
    later_yos = [7, 12, 17, 22, 27, 32, 37]

    for band_label, age in AGE_MAP.items():
        count_line = _extract_matching_line(lines, rf"^\s*{re.escape(band_label)}\s")
        count_payload = re.sub(rf"^\s*{re.escape(band_label)}\s*", "", count_line)
        count_vals = [
            int(token.replace(",", "")) for token in re.findall(r"\d[\d,]*", count_payload)
        ]
        if len(count_vals) < 6:
            raise ValueError(f"Unexpected count row for {band_label}: {count_line}")
        count_vals = count_vals[:-1]

        salary_line_idx = lines.index(count_line) + 1
        salary_line = lines[salary_line_idx]
        salary_vals = [
            float(token.replace(",", "")) for token in re.findall(r"\$([\d,]+)", salary_line)
        ]
        if len(salary_vals) < 6:
            raise ValueError(f"Unexpected salary row for {band_label}: {salary_line}")
        salary_vals = salary_vals[:-1]
        if len(salary_vals) != len(count_vals):
            raise ValueError(f"Unexpected salary row for {band_label}: {salary_line}")

        early_counts = count_vals[:4]
        early_salaries = salary_vals[:4]
        collapsed_count = sum(early_counts)
        collapsed_salary = (
            sum(c * s for c, s in zip(early_counts, early_salaries, strict=False)) / collapsed_count
        )

        count_rows.append({"age": age, "yos": 2, "count": collapsed_count})
        salary_rows.append({"age": age, "yos": 2, "salary": collapsed_salary})

        for yos, count_val, salary_val in zip(
            later_yos, count_vals[4:], salary_vals[4:], strict=False
        ):
            if count_val == 0:
                continue
            count_rows.append({"age": age, "yos": yos, "count": count_val})
            salary_rows.append({"age": age, "yos": yos, "salary": salary_val})

    headcount = pd.DataFrame(count_rows).sort_values(["age", "yos"]).reset_index(drop=True)
    salary = pd.DataFrame(salary_rows).sort_values(["age", "yos"]).reset_index(drop=True)
    return headcount, salary


def _parse_salary_growth() -> pd.DataFrame:
    text = _pdf_page_text(PDF_PATH, SALARY_GROWTH_PDF_PAGE)
    lines = text.splitlines()
    rows: list[dict] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        is_25_up = len(parts) >= 3 and parts[:3] == ["25", "&", "up"]
        if not parts or not (parts[0].isdigit() or is_25_up):
            continue
        if is_25_up:
            yos_label = "25 & up"
            total_pct = parts[-1]
        else:
            yos_label = parts[0]
            total_pct = parts[-1]
        total_pct = total_pct.rstrip("%")
        total = float(total_pct) / 100.0
        if yos_label == "25 & up":
            for yos in range(24, 71):
                rows.append({"yos": yos, "salary_increase": total})
        else:
            src_yos = int(yos_label)
            rows.append({"yos": src_yos - 1, "salary_increase": total})

    out = pd.DataFrame(rows).sort_values("yos").reset_index(drop=True)
    if out.empty:
        raise ValueError("Failed to parse salary growth table from AV")
    return out


def _parse_entrant_profile() -> pd.DataFrame:
    text = _pdf_page_text(PDF_PATH, ENTRANT_PROFILE_PDF_PAGE)
    lines = text.splitlines()
    band_counts: dict[str, int] = {}
    band_salary: dict[str, float] = {}

    pattern = re.compile(r"^\s*(\d{2}-\d{2})\s+([\d,]+)\s+\$?([\d,]+)\s*$")
    for line in lines:
        match = pattern.match(line)
        if not match:
            continue
        band, count_str, salary_str = match.groups()
        band_counts[band] = int(count_str.replace(",", ""))
        band_salary[band] = float(salary_str.replace(",", ""))

    if set(band_counts) != set(ENTRANT_AGE_BANDS):
        missing = sorted(set(ENTRANT_AGE_BANDS) - set(band_counts))
        raise ValueError(f"Missing entrant-profile bands: {missing}")

    canonical_ages = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65]
    count_map = {
        20: ["15-19", "20-24"],
        25: ["20-24"],
        30: ["25-29"],
        35: ["30-34"],
        40: ["35-39"],
        45: ["40-44"],
        50: ["45-49"],
        55: ["50-54"],
        60: ["55-59"],
        65: ["60-64", "65-69"],
    }
    salary_map = {
        20: ["15-19", "20-24"],
        25: ["20-24", "25-29"],
        30: ["25-29", "30-34"],
        35: ["30-34", "35-39"],
        40: ["35-39", "40-44"],
        45: ["40-44", "45-49"],
        50: ["45-49", "50-54"],
        55: ["50-54", "55-59"],
        60: ["55-59", "60-64"],
        65: ["60-64", "65-69"],
    }

    rows: list[dict] = []
    total_count = 0
    for age in canonical_ages:
        count = sum(band_counts[band] for band in count_map[age])
        start_salary = sum(band_salary[band] for band in salary_map[age]) / 2.0
        total_count += count
        rows.append({"entry_age": age, "start_salary": start_salary, "_count": count})

    for row in rows:
        row["entrant_dist"] = row["_count"] / total_count

    return (
        pd.DataFrame(rows)[["entry_age", "start_salary", "entrant_dist"]]
        .sort_values("entry_age")
        .reset_index(drop=True)
    )


def _parse_reduction_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    text = _pdf_page_text(PDF_PATH, REDUCTION_PDF_PAGE)
    lines = text.splitlines()

    gft_rows: list[dict] = []
    others_rows: list[dict] = []

    gft_pattern = re.compile(
        r"^\s*(20|21|22|23|24|25|26|27|28|29|30 or more)\s+"
        r"(\d+)%\s+(\d+)%\s+(\d+)%\s+(\d+)%\s+(\d+)%\s+(\d+)%\s*$"
    )
    for line in lines:
        match = gft_pattern.match(line)
        if not match:
            continue
        yos_label, *pct_vals = match.groups()
        yos = 30 if yos_label == "30 or more" else int(yos_label)
        for age, pct_val in zip(range(55, 61), pct_vals, strict=False):
            gft_rows.append(
                {
                    "age": age,
                    "yos": yos,
                    "reduce_factor": int(pct_val) / 100.0,
                    "tier": "grandfathered",
                }
            )

    others_line = _extract_matching_line(lines, r"^\s*43%\s+46%\s+50%\s+55%")
    other_pcts = [int(token) for token in re.findall(r"(\d+)%", others_line)]
    for age, pct_val in zip(range(55, 66), other_pcts, strict=False):
        others_rows.append({"age": age, "reduce_factor": pct_val / 100.0, "tier": "others"})

    gft = pd.DataFrame(gft_rows).sort_values(["age", "yos"]).reset_index(drop=True)
    others = pd.DataFrame(others_rows).sort_values("age").reset_index(drop=True)
    if gft.empty or others.empty:
        raise ValueError("Failed to parse reduction tables from AV")
    return gft, others


def _parse_termination_rates() -> pd.DataFrame:
    text = _pdf_page_text(PDF_PATH, TERMINATION_PDF_PAGE)
    lines = text.splitlines()
    rows: list[dict] = []

    yos_pairs: list[tuple[int, float]] = []
    for line in lines:
        match = re.match(r"^\s*(\d+)\s+([0-9]+\.[0-9]+)\s*$", line)
        if match:
            service_year, rate = match.groups()
            yos_pairs.append((int(service_year), float(rate)))

    if len(yos_pairs) != 10:
        raise ValueError(f"Unexpected YOS termination rows: {yos_pairs}")

    for service_year, rate in yos_pairs:
        rows.append(
            {
                "lookup_type": "yos",
                "age": pd.NA,
                "lookup_value": service_year - 1,
                "term_rate": rate,
            }
        )

    rows.append(
        {
            "lookup_type": "years_from_nr",
            "age": pd.NA,
            "lookup_value": 0,
            "term_rate": 0.0,
        }
    )

    nr_matches = re.findall(r"(\d+)\s+([0-9]+\.[0-9]+)", text)
    nr_pairs = [(int(k), float(v)) for k, v in nr_matches if int(k) <= 32]
    nr_pairs = nr_pairs[-32:]
    if len(nr_pairs) != 32 or nr_pairs[0][0] != 1 or nr_pairs[-1][0] != 32:
        raise ValueError(f"Unexpected years-from-NR rows: {nr_pairs}")

    for years_from_nr, rate in sorted(nr_pairs):
        rows.append(
            {
                "lookup_type": "years_from_nr",
                "age": pd.NA,
                "lookup_value": years_from_nr,
                "term_rate": rate,
            }
        )

    out = pd.DataFrame(rows)
    order = pd.CategoricalDtype(["yos", "years_from_nr"], ordered=True)
    out["lookup_type"] = out["lookup_type"].astype(order)
    out = out.sort_values(["lookup_type", "lookup_value"]).reset_index(drop=True)
    out["lookup_type"] = out["lookup_type"].astype(str)
    return out


def _parse_retirement_rates() -> pd.DataFrame:
    text = _pdf_page_text(PDF_PATH, RETIREMENT_PDF_PAGE)
    lines = text.splitlines()
    normal_rates: dict[int, float] = dict.fromkeys(range(45, 121), 0.0)
    early_rates: dict[int, float] = dict.fromkeys(range(45, 121), 0.0)

    single_age_normal = re.compile(
        r"^\s*(5[0-9]|6[0-4])\s+([0-9]+\.[0-9]+)\s+([0-9]+\.[0-9]+)\s+(4[5-9]|5[0-9])\s+([0-9]+\.[0-9]+)\s*$"
    )
    band_with_early = re.compile(
        r"^\s*(65-69|70-74|75\+)\s+([0-9]+\.[0-9]+)\s+([0-9]+\.[0-9]+)\s+(6[0-2])\s+([0-9]+\.[0-9]+)\s*$"
    )
    early_only = re.compile(r"^\s*(6[0-4])\s+([0-9]+\.[0-9]+)\s*$")
    continuation_early = re.compile(r"^\s+(6[3-4])\s+([0-9]+\.[0-9]+)\s*$")

    for line in lines:
        match = single_age_normal.match(line)
        if match:
            norm_age, male, female, early_age, early_rate = match.groups()
            normal_rates[int(norm_age)] = (float(male) + float(female)) / 2.0
            early_rates[int(early_age)] = float(early_rate)
            continue

        match = band_with_early.match(line)
        if match:
            band, male, female, early_age, early_rate = match.groups()
            avg_rate = (float(male) + float(female)) / 2.0
            if band == "65-69":
                ages = range(65, 70)
            elif band == "70-74":
                ages = range(70, 75)
            else:
                ages = range(75, 121)
                avg_rate = 1.0
            for age in ages:
                normal_rates[age] = avg_rate
            early_rates[int(early_age)] = float(early_rate)
            continue

        match = early_only.match(line)
        if match:
            early_age, early_rate = match.groups()
            early_rates[int(early_age)] = float(early_rate)
            continue

        match = continuation_early.match(line)
        if match:
            early_age, early_rate = match.groups()
            early_rates[int(early_age)] = float(early_rate)

    rows: list[dict] = []
    for age in range(45, 121):
        rows.append(
            {"age": age, "tier": "all", "retire_type": "early", "retire_rate": early_rates[age]}
        )
    for age in range(45, 121):
        rows.append(
            {"age": age, "tier": "all", "retire_type": "normal", "retire_rate": normal_rates[age]}
        )
    return pd.DataFrame(rows)


def _parse_init_funding() -> pd.DataFrame:
    table2_lines = _pdf_page_text(PDF_PATH, TABLE2_PDF_PAGE).splitlines()
    table4_lines = _pdf_page_text(PDF_PATH, TABLE4_PDF_PAGE).splitlines()

    total_payroll = _extract_first_money_after_label(
        table2_lines, r"^\s*10\.\s*Projected Payroll for Contributions\s*"
    )
    total_aal = _extract_first_money_after_label(
        table2_lines, r"^\s*7\.\s*Actuarial Accrued Liability\s*"
    )
    total_ava = _extract_first_money_after_label(
        table2_lines, r"^\s*8\.\s*Actuarial Value of Assets\s*"
    )
    admin_exp_rate = _extract_first_percent_after_label(
        table2_lines, r"^\s*c\.\s*Administrative expenses\s*"
    )
    total_mva = _extract_first_money_after_label(
        table4_lines, r"^\s*6\.\s*Market value of assets at end of year\s*"
    )

    remaining_2023_line = _extract_matching_line(table4_lines, r"^\s*2023\s")
    remaining_tokens = re.findall(r"\(?[\d,]+\)?", remaining_2023_line)
    if len(remaining_tokens) < 5:
        raise ValueError(f"Unexpected Table 4 2023 deferral row: {remaining_2023_line}")
    remaining_after_valuation = -float(
        remaining_tokens[-1].replace("(", "").replace(")", "").replace(",", "")
    )

    total_ual_ava = total_aal - total_ava
    total_ual_mva = total_aal - total_mva
    fr_ava = total_ava / total_aal
    fr_mva = total_mva / total_aal

    row = {
        "year": 2024,
        "total_payroll": total_payroll,
        "admin_exp_rate": admin_exp_rate,
        "total_aal": total_aal,
        "aal_legacy": total_aal,
        "aal_new": 0.0,
        "total_ava": total_ava,
        "ava_legacy": total_ava,
        "ava_new": 0.0,
        "total_mva": total_mva,
        "mva_legacy": total_mva,
        "mva_new": 0.0,
        "total_ual_ava": total_ual_ava,
        "ual_ava_legacy": total_ual_ava,
        "ual_ava_new": 0.0,
        "total_ual_mva": total_ual_mva,
        "ual_mva_legacy": total_ual_mva,
        "ual_mva_new": 0.0,
        "fr_ava": fr_ava,
        "fr_mva": fr_mva,
        "defer_y1_legacy": 0.0,
        "defer_y2_legacy": remaining_after_valuation,
        "defer_y3_legacy": 0.0,
        "defer_y4_legacy": 0.0,
        "defer_y1_new": 0.0,
        "defer_y2_new": 0.0,
        "defer_y3_new": 0.0,
        "defer_y4_new": 0.0,
    }
    return pd.DataFrame([row])


def _parse_table18_life_annuities() -> dict[str, dict[str, float]]:
    """Read Table 18 (Distribution of Life Annuities by Age) from the AV PDF.

    Returns a dict keyed by published band label with per-band published count
    and annual annuity total. Validates against the published "Total" row.
    """
    text = _pdf_page_text(PDF_PATH, TABLE18_PDF_PAGE)
    lines = text.splitlines()
    bands: dict[str, dict[str, float]] = {}
    for label in LIFE_ANNUITY_BAND_TO_RUNTIME.keys():
        line_re = re.compile(rf"^\s*{re.escape(label)}\s+([\d,]+)\s+\$?\s*([\d,]+)")
        match = None
        for line in lines:
            m = line_re.match(line)
            if m:
                match = m
                break
        if match is None:
            raise ValueError(f"Could not find AV Table 18 band: {label!r}")
        bands[label] = {
            "count": int(match.group(1).replace(",", "")),
            "annual": float(match.group(2).replace(",", "")),
        }

    total_count = sum(b["count"] for b in bands.values())
    total_annual = sum(b["annual"] for b in bands.values())
    if total_count != LIFE_ANNUITY_TOTAL_COUNT:
        raise ValueError(
            f"AV Table 18 count total {total_count} != published {LIFE_ANNUITY_TOTAL_COUNT}"
        )
    if abs(total_annual - LIFE_ANNUITY_TOTAL_ANNUAL) > 1.0:
        raise ValueError(
            f"AV Table 18 annuity total {total_annual} != published {LIFE_ANNUITY_TOTAL_ANNUAL}"
        )
    return bands


def _build_retiree_distribution() -> pd.DataFrame:
    raw = _parse_table18_life_annuities()

    runtime_agg: dict[tuple[int, int], dict[str, float]] = {}
    for label, key in LIFE_ANNUITY_BAND_TO_RUNTIME.items():
        agg = runtime_agg.setdefault(key, {"count": 0.0, "annual": 0.0})
        agg["count"] += raw[label]["count"]
        agg["annual"] += raw[label]["annual"]

    rows: list[dict] = []
    for (lo, hi), agg in sorted(runtime_agg.items()):
        n_ages = hi - lo + 1
        per_age_count = agg["count"] / n_ages
        per_age_total = agg["annual"] / n_ages
        per_age_avg = agg["annual"] / agg["count"]
        for age in range(lo, hi + 1):
            rows.append(
                {
                    "age": age,
                    "count": per_age_count,
                    "avg_benefit": per_age_avg,
                    "total_benefit": per_age_total,
                }
            )

    return pd.DataFrame(rows).sort_values("age").reset_index(drop=True)


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Wrote {path}")


def main() -> None:
    headcount, salary = _parse_table17()
    entrant_profile = _parse_entrant_profile()
    salary_growth = _parse_salary_growth()
    reduction_gft, reduction_others = _parse_reduction_tables()
    retirement_rates = _parse_retirement_rates()
    termination_rates = _parse_termination_rates()
    init_funding = _parse_init_funding()
    retiree_distribution = _build_retiree_distribution()

    _write_csv(headcount, OUT_DIR / "demographics" / "all_headcount.csv")
    _write_csv(salary, OUT_DIR / "demographics" / "all_salary.csv")
    _write_csv(entrant_profile, OUT_DIR / "demographics" / "entrant_profile.csv")
    _write_csv(salary_growth, OUT_DIR / "demographics" / "salary_growth.csv")
    _write_csv(retiree_distribution, OUT_DIR / "demographics" / "retiree_distribution.csv")
    _write_csv(reduction_gft, OUT_DIR / "decrements" / "reduction_gft.csv")
    _write_csv(reduction_others, OUT_DIR / "decrements" / "reduction_others.csv")
    _write_csv(retirement_rates, OUT_DIR / "decrements" / "all_retirement_rates.csv")
    _write_csv(termination_rates, OUT_DIR / "decrements" / "all_termination_rates.csv")
    _write_csv(init_funding, OUT_DIR / "funding" / "init_funding.csv")


if __name__ == "__main__":
    main()
