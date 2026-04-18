#!/usr/bin/env python3
"""
Build first-cut txtrs-av runtime inputs directly from the local 2024 valuation PDF.

Current scope:
  - demographics/all_headcount.csv
  - demographics/all_salary.csv
  - demographics/entrant_profile.csv
  - demographics/salary_growth.csv
  - decrements/reduction_gft.csv
  - decrements/reduction_others.csv

This script intentionally avoids using existing txtrs runtime files as inputs.
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import re
import subprocess

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = PROJECT_ROOT / "prep" / "txtrs-av" / "sources" / "Texas TRS Valuation 2024.pdf"
OUT_DIR = PROJECT_ROOT / "plans" / "txtrs-av" / "data"

TABLE17_PDF_PAGE = 48
SALARY_GROWTH_PDF_PAGE = 70
ENTRANT_PROFILE_PDF_PAGE = 76
REDUCTION_PDF_PAGE = 54

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


def _parse_table17() -> tuple[pd.DataFrame, pd.DataFrame]:
    text = _pdf_page_text(PDF_PATH, TABLE17_PDF_PAGE)
    lines = text.splitlines()

    count_rows: list[dict] = []
    salary_rows: list[dict] = []
    later_yos = [7, 12, 17, 22, 27, 32, 37]

    for band_label, age in AGE_MAP.items():
        count_line = _extract_matching_line(lines, rf"^\s*{re.escape(band_label)}\s")
        count_payload = re.sub(rf"^\s*{re.escape(band_label)}\s*", "", count_line)
        count_vals = [int(token.replace(",", "")) for token in re.findall(r"\d[\d,]*", count_payload)]
        if len(count_vals) < 6:
            raise ValueError(f"Unexpected count row for {band_label}: {count_line}")
        count_vals = count_vals[:-1]

        salary_line_idx = lines.index(count_line) + 1
        salary_line = lines[salary_line_idx]
        salary_vals = [float(token.replace(",", "")) for token in re.findall(r"\$([\d,]+)", salary_line)]
        if len(salary_vals) < 6:
            raise ValueError(f"Unexpected salary row for {band_label}: {salary_line}")
        salary_vals = salary_vals[:-1]
        if len(salary_vals) != len(count_vals):
            raise ValueError(f"Unexpected salary row for {band_label}: {salary_line}")

        early_counts = count_vals[:4]
        early_salaries = salary_vals[:4]
        collapsed_count = sum(early_counts)
        collapsed_salary = sum(c * s for c, s in zip(early_counts, early_salaries)) / collapsed_count

        count_rows.append({"age": age, "yos": 2, "count": collapsed_count})
        salary_rows.append({"age": age, "yos": 2, "salary": collapsed_salary})

        for yos, count_val, salary_val in zip(later_yos, count_vals[4:], salary_vals[4:]):
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
        for age, pct_val in zip(range(55, 61), pct_vals):
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
    for age, pct_val in zip(range(55, 66), other_pcts):
        others_rows.append({"age": age, "reduce_factor": pct_val / 100.0, "tier": "others"})

    gft = pd.DataFrame(gft_rows).sort_values(["age", "yos"]).reset_index(drop=True)
    others = pd.DataFrame(others_rows).sort_values("age").reset_index(drop=True)
    if gft.empty or others.empty:
        raise ValueError("Failed to parse reduction tables from AV")
    return gft, others


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Wrote {path}")


def main() -> None:
    headcount, salary = _parse_table17()
    entrant_profile = _parse_entrant_profile()
    salary_growth = _parse_salary_growth()
    reduction_gft, reduction_others = _parse_reduction_tables()

    _write_csv(headcount, OUT_DIR / "demographics" / "all_headcount.csv")
    _write_csv(salary, OUT_DIR / "demographics" / "all_salary.csv")
    _write_csv(entrant_profile, OUT_DIR / "demographics" / "entrant_profile.csv")
    _write_csv(salary_growth, OUT_DIR / "demographics" / "salary_growth.csv")
    _write_csv(reduction_gft, OUT_DIR / "decrements" / "reduction_gft.csv")
    _write_csv(reduction_others, OUT_DIR / "decrements" / "reduction_others.csv")


if __name__ == "__main__":
    main()
