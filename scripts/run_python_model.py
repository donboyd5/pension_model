"""
Run Python Pension Model and compare against R baseline.

This script:
1. Loads configuration from R baseline
2. Initializes Python model with same parameters
3. Runs workforce projection for each class
4. Compares results against R baseline
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def load_baseline_params() -> Dict[str, Any]:
    """Load R baseline parameters."""
    with open("baseline_outputs/input_params.json", "r") as f:
        data = json.load(f)
    # Convert lists to single values
    return {k: v[0] if isinstance(v, list) else v for k, v in data.items()}


def load_baseline_workforce(class_name: str) -> Dict[str, pd.DataFrame]:
    """Load R baseline workforce data for a class."""
    baseline_dir = Path("baseline_outputs")
    data = {}

    for data_type in ["active", "term", "refund", "retire"]:
        file_path = baseline_dir / f"{class_name}_wf_{data_type}.csv"
        if file_path.exists():
            data[data_type] = pd.read_csv(file_path)

    return data


def compare_workforce(
    python_df: pd.DataFrame,
    r_df: pd.DataFrame,
    value_col: str,
    tolerance: float = 0.05
) -> Dict[str, Any]:
    """Compare workforce data between Python and R."""
    if python_df.empty or r_df.empty:
        return {"status": "missing_data", "python_rows": len(python_df), "r_rows": len(r_df)}

    # Aggregate by year for comparison
    python_by_year = python_df.groupby("year")[value_col].sum()
    r_by_year = r_df.groupby("year")[value_col].sum()

    # Align years
    common_years = python_by_year.index.intersection(r_by_year.index)

    if len(common_years) == 0:
        return {"status": "no_common_years"}

    # Calculate differences
    differences = []
    for year in common_years:
        py_val = python_by_year[year]
        r_val = r_by_year[year]
        if r_val != 0:
            pct_diff = abs(py_val - r_val) / abs(r_val) * 100
        else:
            pct_diff = 100 if py_val != 0 else 0

        differences.append({
            "year": year,
            "python": py_val,
            "r": r_val,
            "pct_diff": pct_diff,
            "passed": pct_diff <= tolerance * 100
        })

    # Summary
    passed = sum(1 for d in differences if d["passed"])
    failed = len(differences) - passed
    max_diff = max(d["pct_diff"] for d in differences)
    avg_diff = sum(d["pct_diff"] for d in differences) / len(differences)

    return {
        "status": "compared",
        "years_compared": len(common_years),
        "passed": passed,
        "failed": failed,
        "max_pct_diff": max_diff,
        "avg_pct_diff": avg_diff,
        "details": differences[:5]  # First5 years
    }


def main():
    """Main function to run Python model and compare to R baseline."""
    print("=" * 60)
    print("Florida FRS Pension Model - Python vs R Comparison")
    print("=" * 60)

    # Load baseline parameters
    print("\n1. Loading R baseline parameters...")
    params = load_baseline_params()
    print(f"   Start year: {params['start_year']}")
    print(f"   Model period: {params['model_period']} years")
    print(f"   Discount rate: {params['dr_current']}")
    print(f"   Payroll growth: {params['payroll_growth']}")

    # Define classes
    classes = [
        "regular",
        "special",
        "admin",
        "eco",
        "eso",
        "judges",
        "senior_management"
    ]

    # Compare workforce data
    print("\n2. Comparing workforce data...")
    print("-" * 60)

    all_results = {}

    for class_name in classes:
        print(f"\n{class_name.upper()}")
        print("-" * 40)

        # Load R baseline
        r_data = load_baseline_workforce(class_name)

        if not r_data:
            print(f"  No baseline data found for {class_name}")
            continue

        # For now, just analyze R baseline structure
        # In full implementation, we would run Python model here
        all_results[class_name] = {}

        for data_type, df in r_data.items():
            if df.empty:
                continue

            # Get value column
            value_col = f"n_{data_type}"
            if data_type == "active":
                value_col = "n_active"

            # Summary stats
            total = df[value_col].sum()
            by_year = df.groupby("year")[value_col].sum()

            print(f"  {data_type}:")
            print(f"    Total: {total:,.2f}")
            print(f"    Years: {by_year.index.min()} - {by_year.index.max()}")
            print(f"    Year1 ({by_year.index.min()}): {by_year.iloc[0]:,.2f}")
            print(f"    Final year ({by_year.index.max()}): {by_year.iloc[-1]:,.2f}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\nR Baseline Workforce Data Loaded Successfully")
    print("\nNext steps to complete validation:")
    print("1. Initialize Python model with FRS adapter")
    print("2. Load input data from baseline_outputs/")
    print("3. Run workforce projection for each class")
    print("4. Compare year-by-year results")
    print("5. Document any discrepancies")

    return all_results


if __name__ == "__main__":
    results = main()
