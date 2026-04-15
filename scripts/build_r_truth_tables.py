"""
One-time script to build frozen R truth tables for FRS and TRS.

This script is run ONCE (or whenever the R baseline CSVs change) and writes
the two R-side sheets to `output/truth_tables.xlsx`:
  - frs_R:   FRS plan-wide aggregate from baseline_outputs/frs_funding.csv
             plus summed total_n_active from per-class liability CSVs
  - txtrs_R: TRS plan-wide from R_model/R_model_txtrs/{baseline,funding}_fresh.csv

The two Python sheets (frs_Py, txtrs_Py) are written separately by the CLI
when you run `pension-model frs` or `pension-model txtrs`.

DO NOT modify the R sheets after they are written. They are the frozen
reference baseline; the whole point of the truth table is to have a stable
target that never moves so Python-side drift is immediately visible.

Usage:
    python scripts/build_r_truth_tables.py
"""

from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from pension_model.truth_table import (  # noqa: E402
    build_r_truth_table_frs,
    build_r_truth_table_txtrs,
    upsert_sheet_to_excel,
    format_truth_table_for_log,
    write_diff_sheet_with_formulas,
)


def main():
    baseline_dir = ROOT / "baseline_outputs"
    trs_r_dir = ROOT / "R_model" / "R_model_txtrs"
    out_path = ROOT / "output" / "truth_tables.xlsx"

    print("Building frozen R truth tables")
    print("=" * 60)

    print(f"\n[1/2] FRS from {baseline_dir.relative_to(ROOT)}/")
    frs_r = build_r_truth_table_frs(baseline_dir)
    print(format_truth_table_for_log(frs_r, max_rows=6))
    print(f"  ... ({len(frs_r)} rows total)")

    print(f"\n[2/2] TRS from {trs_r_dir.relative_to(ROOT)}/")
    txtrs_r = build_r_truth_table_txtrs(trs_r_dir)
    print(format_truth_table_for_log(txtrs_r, max_rows=6))
    print(f"  ... ({len(txtrs_r)} rows total)")

    print(f"\nWriting {out_path.relative_to(ROOT)}")
    upsert_sheet_to_excel(frs_r, out_path, "frs_R")
    upsert_sheet_to_excel(txtrs_r, out_path, "txtrs_R")

    # Also write companion CSVs to each plan's baselines directory, where the
    # CLI looks for them when building the --truth-table diff sheet.
    frs_r.to_csv(ROOT / "plans" / "frs" / "baselines" / "r_truth_table.csv", index=False)
    txtrs_r.to_csv(ROOT / "plans" / "txtrs" / "baselines" / "r_truth_table.csv", index=False)

    # Write live-formula diff sheets (Py - R). These reference the *_R and
    # *_Py sheets so they update automatically whenever the pipeline rewrites
    # the Py sheet.
    print("\nWriting diff sheets (live formulas: Py - R)")
    write_diff_sheet_with_formulas(
        out_path, "frs_diff", "frs_R", "frs_Py", n_rows=len(frs_r)
    )
    write_diff_sheet_with_formulas(
        out_path, "txtrs_diff", "txtrs_R", "txtrs_Py", n_rows=len(txtrs_r)
    )

    print("\nDone. The frs_R and txtrs_R sheets are frozen — do not regenerate")
    print("them unless the R baseline CSVs themselves change.")


if __name__ == "__main__":
    main()
