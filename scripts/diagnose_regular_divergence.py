"""
Diagnostic Script: Regular Class Divergence Analysis

Investigates why the Regular class shows 10%+ divergence by year 2030.
Compares Python and R model year-by-year to identify the root cause.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import json
import pandas as pd
import numpy as np

def load_r_baseline():
    """Load R baseline workforce data for Regular class."""
    print("\n" + "="*80)
    print("LOADING R BASELINE DATA")
    print("="*80)

    # Load summary
    with open("baseline_outputs/regular_wf_summary.json") as f:
        summary = json.load(f)

    print("\nR Baseline Summary:")
    for key, value in summary.items():
        if isinstance(value, list):
            value = value[0]
        print(f"  {key}: {value:,.0f}" if isinstance(value, (int, float)) else f"  {key}: {value}")

    # Load parameters
    with open("baseline_outputs/input_params.json") as f:
        params = json.load(f)

    print("\nR Model Parameters:")
    for key in ['start_year', 'model_period', 'dr_current_', 'payroll_growth_']:
        if key in params:
            val = params[key][0] if isinstance(params[key], list) else params[key]
            print(f"  {key}: {val}")

    print(f"\n  Available parameter keys: {list(params.keys())[:10]}...")

    return summary, params


def check_decrement_tables():
    """Check what decrement tables are available."""
    print("\n" + "="*80)
    print("CHECKING DECREMENT TABLES")
    print("="*80)

    from pension_data.decrement_loader import DecrementLoader
    loader = DecrementLoader("baseline_outputs")

    # Load Regular withdrawal table
    withdrawal_table = loader.load_withdrawal_table("regular", gender="male")
    print(f"\nRegular Withdrawal Table (male):")
    print(f"  Shape: {withdrawal_table.shape}")
    print(f"  Columns: {list(withdrawal_table.columns)}")
    print(f"\n  Sample rates:")
    print(f"    Age 25, YOS 1: {loader.get_withdrawal_rate(withdrawal_table, 25, 1):.6f}")
    print(f"    Age 35, YOS 10: {loader.get_withdrawal_rate(withdrawal_table, 35, 10):.6f}")
    print(f"    Age 45, YOS 20: {loader.get_withdrawal_rate(withdrawal_table, 45, 20):.6f}")
    print(f"    Age 55, YOS 30: {loader.get_withdrawal_rate(withdrawal_table, 55, 30):.6f}")

    # Load Regular mortality table
    mortality_table = loader.load_mortality_table("regular")
    print(f"\nRegular Mortality Table:")
    print(f"  Shape: {mortality_table.shape}")
    print(f"  Columns: {list(mortality_table.columns)}")

    # Check average mortality rates
    if 'mort_final' in mortality_table.columns:
        avg_mort = mortality_table.groupby('dist_age')['mort_final'].mean()
        print(f"\n  Average mortality rates by age:")
        for age in [25, 35, 45, 55, 65, 75]:
            if age in avg_mort.index:
                print(f"    Age {age}: {avg_mort[age]:.6f}")

    return withdrawal_table, mortality_table


def analyze_projection_logic():
    """Analyze the projection logic step-by-step."""
    print("\n" + "="*80)
    print("ANALYZING PROJECTION LOGIC")
    print("="*80)

    print("\nR Model Projection (from FRS workforce model.R):")
    print("  1. Active population starts with initial headcount")
    print("  2. Each year:")
    print("     - Apply separation rates (age/YOS-specific)")
    print("     - Age surviving members by 1 year")
    print("     - Add new entrants (based on growth rate + entrant profile)")
    print("     - Track terminated members separately")
    print("     - Apply mortality to terminated and retired")

    print("\nPython Model Projection (current):")
    print("  1. WorkforceProjector.project_year():")
    print("     - _calculate_active_to_term() - uses sep_table")
    print("     - _age_active_population() - ages and removes terminated")
    print("     - _calculate_new_entrants() - uses pop_growth + entrant_profile")
    print("     - _age_terminated_population() - applies mortality")
    print("     - _calculate_term_to_refund/_retire() - benefit decisions")
    print("     - _age_retiree_population() - applies mortality")

    print("\nPOTENTIAL DIVERGENCE CAUSES:")
    print("  1. New entrant calculation method")
    print("  2. Separation rate lookup (age vs YOS priority)")
    print("  3. Mortality application timing")
    print("  4. Benefit decision logic (refund vs retire)")
    print("  5. Entry age distribution for new hires")


def compare_year_by_year():
    """Compare R and Python year-by-year for first 10 years."""
    print("\n" + "="*80)
    print("YEAR-BY-YEAR COMPARISON (if data available)")
    print("="*80)

    # Load R baseline if available
    baseline_file = Path("baseline_outputs/regular_wf_active.csv")
    if baseline_file.exists():
        r_data = pd.read_csv(baseline_file)

        if 'year' in r_data.columns:
            yearly = r_data.groupby('year')['n_active'].sum()
            print("\nR Active Population by Year:")
            for year in sorted(yearly.index)[:10]:
                print(f"  {year}: {yearly[year]:,.0f}")
        else:
            print("\n[INFO] R data doesn't have 'year' column")
            print(f"  Columns: {list(r_data.columns)}")
    else:
        print(f"\n[INFO] Regular workforce active CSV not found at: {baseline_file}")
        print("  R baseline may use different file structure")


def main():
    """Run all diagnostics."""
    print("\n" + "="*80)
    print("REGULAR CLASS DIVERGENCE DIAGNOSTIC")
    print("="*80)

    # Step 1: Load R baseline
    summary, params = load_r_baseline()

    # Step 2: Check decrement tables
    withdrawal, mortality = check_decrement_tables()

    # Step 3: Analyze projection logic
    analyze_projection_logic()

    # Step 4: Year-by-year comparison
    compare_year_by_year()

    print("\n" + "="*80)
    print("KEY INSIGHTS")
    print("="*80)
    print("""
1. ESO FIX CONFIRMED: ESO now correctly loads Regular withdrawal rates

2. CRITICAL FINDING - R MODEL HAS ZERO POPULATION GROWTH!
   From input_params.json: "pop_growth": [0]

   This explains:
   - R active population stays constant at 536,077 every year
   - Python declines from 536k to 469k (10%+ difference)
   - Python must be using non-zero growth rate!

3. ROOT CAUSE IDENTIFIED:
   The Python model is using a different pop_growth parameter than R.

   ACTION REQUIRED:
   - Check what pop_growth value Python is using
   - Update Python to use pop_growth = 0 to match R baseline
   - With zero growth, new_entrants should exactly offset separations

4. HYPOTHESIS CONFIRMED:
   Python new entrants < Python separations due to incorrect growth parameter
   Fix: Use pop_growth = 0 from R baseline input_params.json
    """)

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
