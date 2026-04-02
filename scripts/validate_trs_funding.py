"""Validate TRS funding model output against R's funding_fresh.csv."""
import sys
sys.path.insert(0, "d:/python_projects/pension_model/src")
import pandas as pd
import numpy as np

py = pd.read_csv("d:/python_projects/pension_model/output/txtrs/funding.csv")
r = pd.read_csv("d:/python_projects/pension_model/R_model/R_model_txtrs/funding_fresh.csv")

# Key columns to compare
key_cols = [
    ("payroll", "payroll"),
    ("AAL", "AAL"),
    ("AAL_legacy", "AAL_legacy"),
    ("AVA", "AVA"),
    ("MVA", "MVA"),
    ("FR_AVA", "FR_AVA"),
    ("FR_MVA", "FR_MVA"),
    ("UAL_AVA", "UAL_AVA"),
    ("nc_rate", "nc_rate"),
    ("nc_legacy", "nc_legacy"),
    ("nc_new", "nc_new"),
    ("er_cont", "er_cont"),
    ("er_cont_rate", "er_cont_rate"),
    ("tot_cont_rate", "tot_cont_rate"),
    ("ben_payment_legacy", "ben_payment_legacy"),
    ("er_amo_cont_legacy", "er_amo_cont_legacy"),
    ("er_stat_eff_rate", "er_stat_eff_rate"),
    ("amo_rate_legacy", "amo_rate_legacy"),
]

print(f"Python rows: {len(py)}, R rows: {len(r)}")
print(f"Python years: {py['year'].min()}-{py['year'].max()}")
print(f"R years: {r['fy'].min()}-{r['fy'].max()}")

# Align on year
r_aligned = r.rename(columns={"fy": "year"})
comp = py.merge(r_aligned[["year"] + [c[1] for c in key_cols if c[1] in r_aligned.columns]],
                on="year", suffixes=("_py", "_r"), how="inner")

print(f"\nMatched years: {len(comp)}")
print(f"\n{'Column':<25} {'Year':>4} {'Python':>16} {'R':>16} {'%Diff':>10}")
print("-" * 75)

for py_col, r_col in key_cols:
    py_c = f"{py_col}_py" if f"{py_col}_py" in comp.columns else py_col
    r_c = f"{r_col}_r" if f"{r_col}_r" in comp.columns else r_col
    if py_c not in comp.columns or r_c not in comp.columns:
        print(f"{py_col:<25} MISSING")
        continue

    # Skip year 0 (initial values, may have NAs in R)
    for idx in [1, 5, 15, 30]:  # years 2, 6, 16, 31 (index from 0)
        if idx >= len(comp):
            continue
        row = comp.iloc[idx]
        pv = row[py_c]
        rv = row[r_c]
        if pd.isna(rv) or rv == 0:
            pct = "N/A" if pd.isna(rv) else ("0" if pv == 0 else "inf")
        else:
            pct = f"{(pv - rv) / abs(rv) * 100:.4f}%"
        yr = int(row["year"])
        print(f"{py_col:<25} {yr:>4} {pv:>16.2f} {rv:>16.2f} {pct:>10}")
