"""R-vs-Python truth-table scenario matrix for FRS and TXTRS.

This test is intentionally report-oriented: it compares every configured
plan/scenario cell, writes a CSV summary, and then fails if any cell diverges
from its R truth table beyond floating-point noise.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytestmark = [pytest.mark.invariant, pytest.mark.regression]


REPO_ROOT = Path(__file__).resolve().parents[2]
XLSX_OUT_PATH = REPO_ROOT / "output" / "truth_table_scenario_matrix_by_scenario.xlsx"

PLANS = ("frs", "txtrs")
SCENARIOS = (
    None,
    "high_discount",
    "low_return",
    "no_cola",
    "asset_shock",
    "high_inflation",
    "high_inflation_linked",
)
KEY_COLUMNS = ("aal_boy", "mva_boy", "payroll", "er_cont_total")

REL_TOL = 1e-10
ABS_TOL = 1e-2


def _scenario_name(scenario: str | None) -> str:
    return scenario or "baseline"


def _scenario_path(scenario: str | None) -> Path | None:
    if scenario is None:
        return None
    return REPO_ROOT / "scenarios" / f"{scenario}.json"


def _r_truth_path(plan: str, scenario: str | None) -> Path:
    if scenario is None:
        return REPO_ROOT / "plans" / plan / "baselines" / "r_truth_table.csv"
    return REPO_ROOT / "plans" / plan / "baselines" / f"r_truth_table_{scenario}.csv"


def _build_python_truth_table(plan: str, scenario: str | None) -> pd.DataFrame:
    from pension_model.config_loading import load_plan_config
    from pension_model.core.funding_model import load_funding_inputs, run_funding_model
    from pension_model.core.pipeline import run_plan_pipeline
    from pension_model.truth_table import build_python_truth_table

    constants = load_plan_config(
        REPO_ROOT / "plans" / plan / "config" / "plan_config.json",
        calibration_path=REPO_ROOT / "plans" / plan / "config" / "calibration.json",
        scenario_path=_scenario_path(scenario),
    )
    liability = run_plan_pipeline(constants)
    funding_inputs = load_funding_inputs(constants.resolve_data_dir() / "funding")
    funding = run_funding_model(liability, funding_inputs, constants)
    return build_python_truth_table(plan, liability, funding, constants)


def _numeric_columns(r: pd.DataFrame, py: pd.DataFrame) -> list[str]:
    return [
        col
        for col in r.columns
        if col in py.columns
        and col not in ("plan", "year")
        and pd.api.types.is_numeric_dtype(r[col])
        and pd.api.types.is_numeric_dtype(py[col])
    ]


def _comparison_detail_rows(
    plan: str,
    scenario: str,
    r: pd.DataFrame,
    py: pd.DataFrame,
    common_numeric: list[str],
) -> list[dict[str, object]]:
    merged = r[["year", *common_numeric]].merge(
        py[["year", *common_numeric]],
        on="year",
        suffixes=("_r", "_python"),
        validate="one_to_one",
    )

    rows = [
        {
            "plan": plan,
            "scenario": scenario,
            "year": int(year),
        }
        for year in merged["year"]
    ]
    for col in common_numeric:
        r_col = f"{col}_r"
        py_col = f"{col}_python"
        diff = merged[py_col] - merged[r_col]
        abs_diff = diff.abs()
        rel_diff = abs_diff.div(merged[r_col].abs().replace(0, np.nan)).fillna(0.0)

        for idx, row in enumerate(rows):
            row[f"{col}_r"] = float(merged.at[idx, r_col])
            row[f"{col}_python"] = float(merged.at[idx, py_col])
            row[f"{col}_diff"] = float(diff.iat[idx])
            row[f"{col}_abs_diff"] = float(abs_diff.iat[idx])
            row[f"{col}_rel_diff"] = float(rel_diff.iat[idx])
            row[f"{col}_status"] = (
                "PASS" if abs_diff.iat[idx] <= ABS_TOL or rel_diff.iat[idx] <= REL_TOL else "DIFF"
            )
    return rows


def _compare_cell(plan: str, scenario: str | None) -> tuple[dict[str, object], list[dict[str, object]]]:
    r_path = _r_truth_path(plan, scenario)
    scenario_label = _scenario_name(scenario)

    row: dict[str, object] = {
        "plan": plan,
        "scenario": scenario_label,
        "status": "MISSING_R",
        "r_truth_path": str(r_path.relative_to(REPO_ROOT)),
    }
    if not r_path.exists():
        return row, []

    r = pd.read_csv(r_path)
    py = _build_python_truth_table(plan, scenario)
    common_numeric = _numeric_columns(r, py)
    assert common_numeric, f"No comparable numeric columns for {plan}/{scenario_label}"
    detail_rows = _comparison_detail_rows(plan, scenario_label, r, py, common_numeric)

    worst_col = ""
    worst_abs = -1.0
    worst_rel = 0.0
    mismatched_cols = []

    for col in common_numeric:
        diff = (py[col] - r[col]).abs()
        abs_max = float(diff.max(skipna=True))
        denom = r[col].abs().replace(0, np.nan)
        rel = diff.div(denom).max(skipna=True)
        rel_max = float(rel) if pd.notna(rel) else 0.0

        if abs_max > worst_abs:
            worst_abs = abs_max
            worst_rel = rel_max
            worst_col = col
        if abs_max > ABS_TOL and rel_max > REL_TOL:
            mismatched_cols.append(f"{col}: rel={rel_max:.3e}, abs={abs_max:.3e}")

    final_r = r.iloc[-1]
    final_py = py.iloc[-1]
    for col in KEY_COLUMNS:
        if col in r.columns and col in py.columns:
            row[f"r_final_{col}"] = float(final_r[col])
            row[f"python_final_{col}"] = float(final_py[col])

    row.update(
        {
            "status": "PASS" if not mismatched_cols else "DIFF",
            "worst_col": worst_col,
            "max_abs_diff": worst_abs,
            "max_rel_diff": worst_rel,
            "mismatched_cols": "; ".join(mismatched_cols),
        }
    )
    return row, detail_rows


def _write_scenario_workbook(summary: pd.DataFrame, detail: pd.DataFrame) -> None:
    with pd.ExcelWriter(XLSX_OUT_PATH, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="summary", index=False)
        for scenario in [_scenario_name(s) for s in SCENARIOS]:
            scenario_detail = detail[detail["scenario"] == scenario]
            scenario_detail.to_excel(writer, sheet_name=scenario[:31], index=False)


def test_frs_txtrs_scenario_matrix_matches_r_truth():
    rows = []
    detail_rows = []
    for plan in PLANS:
        for scenario in SCENARIOS:
            row, cell_detail_rows = _compare_cell(plan, scenario)
            rows.append(row)
            detail_rows.extend(cell_detail_rows)

    comparison = pd.DataFrame(rows)
    detail = pd.DataFrame(detail_rows)

    XLSX_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _write_scenario_workbook(comparison, detail)

    print("\nR-vs-Python scenario comparison")
    print(comparison.to_string(index=False))
    print(f"\nWrote {XLSX_OUT_PATH.relative_to(REPO_ROOT)}")

    missing = comparison[comparison["status"] == "MISSING_R"]
    assert missing.empty, (
        "Missing R truth table(s):\n"
        + missing[["plan", "scenario", "r_truth_path"]].to_string(index=False)
    )

    diffs = comparison[comparison["status"] == "DIFF"]
    assert diffs.empty, (
        "R/Python scenario divergence(s):\n"
        + diffs[
            ["plan", "scenario", "worst_col", "max_abs_diff", "max_rel_diff", "mismatched_cols"]
        ].to_string(index=False)
        + f"\nScenario workbook written to {XLSX_OUT_PATH.relative_to(REPO_ROOT)}"
    )
