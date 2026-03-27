"""
Validation script to compare Python model outputs against R baseline.

This script:
1. Loads R baseline data from baseline_outputs/
2. Runs Python model for the same parameters
3. Compares outputs and reports discrepancies
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass


@dataclass
class ComparisonResult:
    """Result of comparing a single metric."""
    metric_name: str
    r_value: float
    python_value: float
    difference: float
    percent_difference: float
    tolerance: float
    passed: bool


def load_baseline_summary(class_name: str) -> Dict[str, Any]:
    """Load R baseline summary for a class."""
    baseline_dir = Path("baseline_outputs")
    summary_file = baseline_dir / f"{class_name}_wf_summary.json"

    if summary_file.exists():
        with open(summary_file, "r") as f:
            data = json.load(f)
        # Convert lists to single values
        return {k: v[0] if isinstance(v, list) else v for k, v in data.items()}
    return {}


def load_baseline_liability_summary(class_name: str) -> Dict[str, Any]:
    """Load R baseline liability summary for a class."""
    baseline_dir = Path("baseline_outputs")
    summary_file = baseline_dir / f"{class_name}_liability_summary.json"

    if summary_file.exists():
        with open(summary_file, "r") as f:
            data = json.load(f)
        # Convert lists to single values
        return {k: v[0] if isinstance(v, list) else v for k, v in data.items()}
    return {}


def load_baseline_workforce_data(class_name: str, data_type: str) -> pd.DataFrame:
    """Load R baseline workforce data for a class."""
    baseline_dir = Path("baseline_outputs")
    file_path = baseline_dir / f"{class_name}_wf_{data_type}.csv"

    if file_path.exists():
        return pd.read_csv(file_path)
    return pd.DataFrame()


def load_baseline_liability_data(class_name: str) -> pd.DataFrame:
    """Load R baseline liability data for a class."""
    baseline_dir = Path("baseline_outputs")
    file_path = baseline_dir / f"{class_name}_liability.csv"

    if file_path.exists():
        return pd.read_csv(file_path)
    return pd.DataFrame()


def compare_values(
    r_value: float,
    python_value: float,
    metric_name: str,
    tolerance: float = 0.05
) -> ComparisonResult:
    """Compare two values and return result."""
    if r_value == 0:
        difference = python_value
        percent_difference = 100 if python_value != 0 else 0
    else:
        difference = python_value - r_value
        percent_difference = abs(difference / r_value) * 100

    passed = percent_difference <= (tolerance * 100)

    return ComparisonResult(
        metric_name=metric_name,
        r_value=r_value,
        python_value=python_value,
        difference=difference,
        percent_difference=percent_difference,
        tolerance=tolerance * 100,
        passed=passed
    )


def validate_workforce_summaries(classes: List[str], tolerance: float = 0.05) -> List[ComparisonResult]:
    """Validate workforce summaries against R baseline."""
    results = []

    for class_name in classes:
        print(f"\nValidating {class_name} workforce summary...")
        baseline = load_baseline_summary(class_name)

        if not baseline:
            print(f"  No baseline found for {class_name}")
            continue

        # For now, just validate that we can load the baseline
        # In a full implementation, we would run the Python model here
        print(f"  Baseline loaded: {baseline}")

        # Compare key metrics
        for metric in ["total_active", "total_terminations", "total_refunds", "total_retirements"]:
            if metric in baseline:
                r_value = baseline[metric]
                print(f"  {metric}: {r_value:,.2f}")

    return results


def validate_liability_summaries(classes: List[str], tolerance: float = 0.05) -> List[ComparisonResult]:
    """Validate liability summaries against R baseline."""
    results = []

    for class_name in classes:
        print(f"\nValidating {class_name} liability summary...")
        baseline = load_baseline_liability_summary(class_name)

        if not baseline:
            print(f"  No baseline found for {class_name}")
            continue

        print(f"  Baseline loaded: {baseline}")

    return results


def validate_workforce_data(classes: List[str]) -> None:
    """Validate workforce data structure and content."""
    for class_name in classes:
        print(f"\nValidating {class_name} workforce data...")

        for data_type in ["active", "term", "refund", "retire"]:
            df = load_baseline_workforce_data(class_name, data_type)
            if not df.empty:
                print(f"  {data_type}: {len(df)} rows, columns: {list(df.columns)}")
            else:
                print(f"  {data_type}: No data")


def validate_liability_data(classes: List[str]) -> None:
    """Validate liability data structure and content."""
    for class_name in classes:
        print(f"\nValidating {class_name} liability data...")

        df = load_baseline_liability_data(class_name)
        if not df.empty:
            print(f"  Liability data: {len(df)} rows, {len(df.columns)} columns")
            print(f"  Years: {df['year'].min()} - {df['year'].max()}")
            print(f"  Sample columns: {list(df.columns[:10])}")
        else:
            print(f"  No liability data")


def main():
    """Main validation function."""
    print("=" *60)
    print("Florida FRS Pension Model - Baseline Validation")
    print("=" * 60)

    # Define classes to validate
    classes = [
        "regular",
        "special",
        "admin",
        "eco",
        "eso",
        "judges",
        "senior_management"
    ]

    # Load and display baseline summaries
    print("\n" + "=" * 60)
    print("1. Workforce Summaries")
    print("=" * 60)
    validate_workforce_summaries(classes)

    print("\n" + "=" * 60)
    print("2. Liability Summaries")
    print("=" * 60)
    validate_liability_summaries(classes)

    print("\n" + "=" * 60)
    print("3. Workforce Data Structure")
    print("=" * 60)
    validate_workforce_data(classes)

    print("\n" + "=" * 60)
    print("4. Liability Data Structure")
    print("=" * 60)
    validate_liability_data(classes)

    print("\n" + "=" * 60)
    print("Baseline Validation Complete")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run Python model with same parameters as R model")
    print("2. Compare outputs using validation framework")
    print("3. Document any discrepancies in issues.md")


if __name__ == "__main__":
    main()
