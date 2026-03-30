"""
Calibrate Python actuarial calculations against R baseline.

This script:
1. Loads full workforce cohorts from R baseline
2. Loads R's retirement decrement tables
3. Applies Python actuarial calculations to all members
4. Aggregates results by year
5. Compares against R baseline values
6. Reports discrepancies and calibration recommendations
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pension_data import DecrementLoader
from pension_tools.actuarial import (
    ActuarialAssumptions,
    ActuarialCalculator,
    create_calculator_for_class
)


# FRS-specific benefit multipliers by class
BENEFIT_MULTIPLIERS = {
    'regular': 0.016,      # 1.6%
    'special': 0.020,      # 2.0%
    'admin': 0.016,        # 1.6%
    'eco': 0.016,          # 1.6%
    'eso': 0.020,          # 2.0%
    'judges': 0.033,       # 3.3%
    'senior_management': 0.020  # 2.0%
}

# Normal retirement ages by class
NORMAL_RETIREMENT_AGES = {
    'regular': 62,
    'special': 55,
    'admin': 62,
    'eco': 62,
    'eso': 55,
    'judges': 60,
    'senior_management': 60
}


def load_baseline_params() -> Dict[str, Any]:
    """Load R baseline parameters."""
    with open("baseline_outputs/input_params.json", "r") as f:
        data = json.load(f)
    return {k: v[0] if isinstance(v, list) else v for k, v in data.items()}


def load_r_liability_data(class_name: str) -> pd.DataFrame:
    """Load R baseline liability data for a class."""
    filepath = f"baseline_outputs/{class_name}_liability.csv"
    return pd.read_csv(filepath)


def load_r_funding_data(class_name: str) -> pd.DataFrame:
    """Load R baseline funding data for a class."""
    filepath = f"baseline_outputs/{class_name}_funding.csv"
    return pd.read_csv(filepath)


def load_r_workforce_data(class_name: str) -> pd.DataFrame:
    """Load R baseline active workforce data for a class."""
    filepath = f"baseline_outputs/{class_name}_wf_active.csv"
    return pd.read_csv(filepath)


def load_r_mortality_data(class_name: str) -> pd.DataFrame:
    """Load R baseline mortality rates for a class."""
    filepath = f"baseline_outputs/{class_name}_mortality_rates.csv"
    return pd.read_csv(filepath)


def load_salary_distribution(class_name: str) -> pd.DataFrame:
    """Load salary distribution for estimating salaries."""
    filepath = f"baseline_outputs/{class_name}_dist_salary.csv"
    try:
        return pd.read_csv(filepath)
    except FileNotFoundError:
        return None


def create_actuarial_calculator(
    class_name: str,
    params: Dict[str, Any],
    mortality_table: pd.DataFrame = None
) -> ActuarialCalculator:
    """
    Create an actuarial calculator for a specific class.

    Args:
        class_name: Membership class name
        params: Baseline parameters
        mortality_table: Optional mortality table DataFrame

    Returns:
        ActuarialCalculator instance
    """
    benefit_multiplier = BENEFIT_MULTIPLIERS.get(class_name, 0.016)
    retirement_age = NORMAL_RETIREMENT_AGES.get(class_name, 62)

    assumptions = ActuarialAssumptions(
        discount_rate=params.get('dr', 0.067),
        salary_growth=params.get('salary_growth', 0.0325),
        cola_rate=params.get('cola', 0.03),
        benefit_multiplier=benefit_multiplier,
        retirement_age=retirement_age,
        max_age=120
    )

    calculator = ActuarialCalculator(
        assumptions=assumptions,
        mort_table=mortality_table
    )

    return calculator


def estimate_salary_from_distribution(
    age: int,
    entry_age: int,
    salary_dist: pd.DataFrame,
    base_salary: float = 50000
) -> float:
    """
    Estimate salary based on age and entry age using distribution data.

    Uses a simple model: salary = base * (1 + growth)^(age - entry_age)
    """
    if salary_dist is not None:
        # Try to find salary for this age in distribution
        # For now, use simple growth model
        pass

    # Default: 3.25% annual salary growth
    yos = max(0, age - entry_age)
    growth_rate = 0.0325
    return base_salary * ((1 + growth_rate) ** yos)


def calculate_cohort_actuarials(
    wf_active: pd.DataFrame,
    calculator: ActuarialCalculator,
    year: int,
    salary_dist: pd.DataFrame = None
) -> Dict[str, float]:
    """
    Calculate actuarial values for entire cohort in a given year.

    Args:
        wf_active: DataFrame with active workforce data (entry_age, age, year, n_active)
        calculator: ActuarialCalculator instance
        year: Year to calculate for
        salary_dist: Optional salary distribution for estimating salaries

    Returns:
        Dictionary with total PVFB, NC, AAL, payroll, and member count
    """
    total_pvfb = 0.0
    total_nc = 0.0
    total_aal = 0.0
    total_payroll = 0.0
    member_count = 0.0

    # Filter for the specified year
    wf_year = wf_active[wf_active['year'] == year].copy()

    if wf_year.empty:
        return {
            'pvfb': 0.0,
            'nc': 0.0,
            'aal': 0.0,
            'payroll': 0.0,
            'member_count': 0
        }

    # Group by entry_age and age
    for _, row in wf_year.iterrows():
        entry_age = int(row.get('entry_age', 30))
        age = int(row.get('age', 45))
        n_active = row.get('n_active', 0)

        if n_active <= 0:
            continue

        yos = age - entry_age
        if yos < 0:
            continue

        # Estimate salary
        salary = estimate_salary_from_distribution(age, entry_age, salary_dist)

        # Calculate actuarial values for this cohort
        try:
            pvfb = calculator.calculate_pvfb(entry_age, age, salary, yos)
            nc = calculator.calculate_normal_cost(entry_age, age, salary, yos)
            aal = calculator.calculate_aal(entry_age, age, salary, yos)

            # Aggregate weighted by headcount
            total_pvfb += pvfb * n_active
            total_nc += nc * n_active
            total_aal += aal * n_active
            total_payroll += salary * n_active
            member_count += n_active
        except Exception as e:
            print(f"  Warning: Error calculating for entry_age={entry_age}, age={age}: {e}")
            continue

    return {
        'pvfb': total_pvfb,
        'nc': total_nc,
        'aal': total_aal,
        'payroll': total_payroll,
        'member_count': member_count
    }


def compare_year_by_year(
    class_name: str,
    years: List[int],
    params: Dict[str, Any]
) -> pd.DataFrame:
    """
    Compare Python vs R actuarial calculations year by year.

    Args:
        class_name: Membership class name
        years: List of years to compare
        params: Baseline parameters

    Returns:
        DataFrame with comparison results
    """
    print(f"\n{'='*60}")
    print(f"Calibrating {class_name.upper()}")
    print(f"{'='*60}")

    # Load R baseline data
    r_liability = load_r_liability_data(class_name)
    r_funding = load_r_funding_data(class_name)
    wf_active = load_r_workforce_data(class_name)
    salary_dist = load_salary_distribution(class_name)

    # Try to load mortality table
    try:
        mortality_df = load_r_mortality_data(class_name)
        print(f"  Loaded mortality table: {len(mortality_df)} records")
    except Exception as e:
        print(f"  Warning: Could not load mortality table: {e}")
        mortality_df = None

    # Create calculator
    calculator = create_actuarial_calculator(class_name, params, mortality_df)

    results = []

    for year in years:
        # Get R baseline values for this year
        r_year = r_liability[r_liability['year'] == year]
        r_fund_year = r_funding[r_funding['year'] == year]

        if r_year.empty:
            continue

        # R baseline values
        r_pvfb = r_year['pvfb_active_db_legacy_est'].values[0]
        r_nc_rate = r_year['nc_rate_db_legacy_est'].values[0]
        r_aal = r_year['aal_active_db_legacy_est'].values[0]
        r_payroll = r_year['payroll_db_legacy_est'].values[0]

        # Calculate Python values
        py_results = calculate_cohort_actuarials(
            wf_active, calculator, year, salary_dist
        )

        # Calculate NC rate
        py_nc_rate = py_results['nc'] / py_results['payroll'] if py_results['payroll'] > 0 else 0

        # Calculate differences
        pvfb_diff = py_results['pvfb'] - r_pvfb
        nc_rate_diff = py_nc_rate - r_nc_rate
        aal_diff = py_results['aal'] - r_aal

        pvfb_pct = (pvfb_diff / r_pvfb * 100) if r_pvfb != 0 else 0
        nc_rate_pct = (nc_rate_diff / r_nc_rate * 100) if r_nc_rate != 0 else 0
        aal_pct = (aal_diff / r_aal * 100) if r_aal != 0 else 0

        results.append({
            'year': year,
            'r_pvfb': r_pvfb,
            'py_pvfb': py_results['pvfb'],
            'pvfb_diff': pvfb_diff,
            'pvfb_pct': pvfb_pct,
            'r_nc_rate': r_nc_rate,
            'py_nc_rate': py_nc_rate,
            'nc_rate_diff': nc_rate_diff,
            'nc_rate_pct': nc_rate_pct,
            'r_aal': r_aal,
            'py_aal': py_results['aal'],
            'aal_diff': aal_diff,
            'aal_pct': aal_pct,
            'r_payroll': r_payroll,
            'py_payroll': py_results['payroll'],
            'member_count': py_results['member_count']
        })

        print(f"  {year}: NC Rate R={r_nc_rate:.4f} Py={py_nc_rate:.4f} " +
              f"({nc_rate_pct:+.2f}%), AAL R={r_aal/1e9:.2f}B Py={py_results['aal']/1e9:.2f}B " +
              f"({aal_pct:+.2f}%)")

    return pd.DataFrame(results)


def run_calibration():
    """Run full calibration for all membership classes."""
    print("=" * 70)
    print("PYTHON ACTUARIAL CALIBRATION AGAINST R BASELINE")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load baseline parameters
    params = load_baseline_params()
    print(f"\nKey Assumptions:")
    print(f"  Discount Rate: {params.get('dr', 0.067)*100:.2f}%")
    print(f"  Salary Growth: {params.get('salary_growth', 0.0325)*100:.2f}%")
    print(f"  COLA: {params.get('cola', 0.03)*100:.2f}%")

    # Classes to calibrate
    classes = ['regular', 'special', 'admin', 'eco', 'eso', 'judges', 'senior_management']

    # Years to analyze
    years = list(range(2022, 2027))  # First 5 years

    all_results = {}
    summary = []

    for class_name in classes:
        try:
            df = compare_year_by_year(class_name, years, params)
            all_results[class_name] = df

            # Calculate average discrepancies
            if not df.empty:
                avg_nc_diff = df['nc_rate_pct'].mean()
                avg_aal_diff = df['aal_pct'].mean()
                summary.append({
                    'class': class_name,
                    'avg_nc_rate_diff_pct': avg_nc_diff,
                    'avg_aal_diff_pct': avg_aal_diff,
                    'years': len(df)
                })
        except Exception as e:
            print(f"  Error calibrating {class_name}: {e}")
            continue

    # Print summary
    print("\n" + "=" * 70)
    print("CALIBRATION SUMMARY")
    print("=" * 70)
    print(f"{'Class':<20} {'Avg NC Rate Diff':>18} {'Avg AAL Diff':>15} {'Years':>8}")
    print("-" * 70)

    for s in summary:
        print(f"{s['class']:<20} {s['avg_nc_rate_diff_pct']:>17.2f}% " +
              f"{s['avg_aal_diff_pct']:>14.2f}% {s['years']:>8}")

    # Save results
    output_dir = Path("baseline_outputs/calibration")
    output_dir.mkdir(exist_ok=True)

    for class_name, df in all_results.items():
        if not df.empty:
            df.to_csv(output_dir / f"{class_name}_calibration.csv", index=False)

    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(output_dir / "calibration_summary.csv", index=False)

    print(f"\nResults saved to: {output_dir}")

    # Analysis and recommendations
    print("\n" + "=" * 70)
    print("ANALYSIS AND RECOMMENDATIONS")
    print("=" * 70)

    # Identify systematic biases
    nc_biases = [s['avg_nc_rate_diff_pct'] for s in summary]
    aal_biases = [s['avg_aal_diff_pct'] for s in summary]

    if np.mean(nc_biases) > 5:
        print("- Python NC rates are systematically HIGHER than R baseline")
        print("  Possible causes:")
        print("    * Retirement age assumptions (using fixed age vs probability-weighted)")
        print("    * Annuity factor calculation differences")
        print("    * Salary projection methodology")

    if np.mean(aal_biases) < -30:
        print("- Python AAL values are systematically LOWER than R baseline")
        print("  Possible causes:")
        print("    * EAN method implementation differences")
        print("    * Survival probability calculation")
        print("    * Retirement probability weighting")

    print("\nNext Steps:")
    print("1. Load R's retirement decrement tables for probability-weighted retirement")
    print("2. Verify annuity factor methodology matches R implementation")
    print("3. Compare survival probability calculations")
    print("4. Validate salary projection against R baseline")

    return all_results, summary


if __name__ == "__main__":
    results, summary = run_calibration()
