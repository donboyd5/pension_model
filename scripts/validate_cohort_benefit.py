"""
Validate Python benefit calculations against R baseline at the cohort level.

Compares per-cohort salary, FAS, db_benefit, PVFB, PVFS, and NC rate
using the R model's extracted benefit_val_table.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def load_params():
    """Load model parameters."""
    with open("baseline_outputs/input_params.json") as f:
        params = json.load(f)
    with open("configs/calibration_params.json") as f:
        cal = json.load(f)
    return params, cal


def build_salary_vector(entry_age, entry_year, entry_salary, sal_growth, payroll_growth, max_yos=71):
    """
    Build salary vector matching R model's salary calculation.

    R code (benefit model line ~655):
    salary = if_else(entry_year <= max(salary_headcount_table$entry_year),
                     entry_salary * cumprod_salary_increase,
                     start_sal * cumprod_salary_increase * (1 + payroll_growth)^(entry_year - max_entry_year))
    """
    # Cumulative salary growth (R: cumprod(1 + lag(salary_increase, default=0)))
    growth_rates = sal_growth['salary_increase_regular'].values
    cumprod = np.ones(max_yos)
    for i in range(1, min(max_yos, len(growth_rates))):
        cumprod[i] = cumprod[i-1] * (1 + growth_rates[min(i-1, len(growth_rates)-1)])
    # Extend beyond table
    for i in range(len(growth_rates), max_yos):
        cumprod[i] = cumprod[i-1] * (1 + growth_rates[-1])

    # R's max entry_year from salary_headcount_table is 2020 (yos=2 band center)
    max_historical_entry_year = 2020

    salary = np.zeros(max_yos)
    for yos in range(max_yos):
        if entry_year <= max_historical_entry_year:
            salary[yos] = entry_salary * cumprod[yos]
        else:
            # For future entrants, use start_sal with payroll growth
            salary[yos] = entry_salary * cumprod[yos] * (1 + payroll_growth) ** (entry_year - max_historical_entry_year)

    return salary


def compute_fas(salary, fas_period=5):
    """
    Compute final average salary (rolling mean).

    R uses baseR.rollmean with a LAG: FAS at yos=t is the average of
    salary at yos (t-fas_period) through (t-1), NOT including current yos.
    """
    fas = np.full(len(salary), np.nan)
    for i in range(fas_period, len(salary)):
        fas[i] = np.mean(salary[i - fas_period:i])
    return fas


def get_benefit_multiplier(tier, yos, age):
    """
    Get benefit multiplier matching R model.

    R code (benefit model lines 722-797):
    Regular Tier 1: 1.60% base, graded up to 1.68% at age 65+ or 33+ YOS
    """
    if 'tier_1' in tier:
        if (age >= 65 and yos >= 6) or yos >= 33:
            return 0.0168
        elif (age >= 64 and yos >= 6) or yos >= 32:
            return 0.0165
        elif (age >= 63 and yos >= 6) or yos >= 31:
            return 0.0163
        elif (age >= 62 and yos >= 6) or yos >= 30:
            return 0.0160
        elif 'early' in tier:
            return 0.0160
        elif 'vested' in tier or 'non_vested' in tier:
            return 0.0160
        else:
            return 0.0160
    elif 'tier_2' in tier:
        return 0.0160  # Tier 2 regular
    elif 'tier_3' in tier:
        return 0.0165  # Tier 3 regular
    return 0.0160


def get_reduce_factor(tier, age):
    """
    Early retirement reduction factor.

    R code: reduce_factor = 1 - 0.05 * (normal_age - dist_age)
    For Regular Tier 1: normal age = 62
    For Regular Tier 2/3: normal age = 65
    """
    if 'early' in tier:
        if 'tier_1' in tier:
            return max(0, 1 - 0.05 * (62 - age))
        else:
            return max(0, 1 - 0.05 * (65 - age))
    return 1.0  # Normal retirement or not yet eligible


def npv(rate, cashflows):
    """Net present value."""
    if len(cashflows) == 0:
        return 0.0
    factors = (1 + rate) ** (-np.arange(1, len(cashflows) + 1))
    return float(np.sum(np.array(cashflows) * factors))


def get_pvfb_r(sep_rate_vec, interest, value_vec):
    """
    Replicate R's get_pvfb function.

    R code (utility_functions.R lines 226-238):
    sep_prob = cumprod(1 - lag(sep_rate, n=2, default=0)) * lag(sep_rate, default=0)
    PVFB[i] = npv(interest, value_adjusted[2:end])
    """
    n = len(value_vec)
    PVFB = np.zeros(n)

    for i in range(n):
        sr = sep_rate_vec[i:]
        val = value_vec[i:]
        m = len(sr)

        # lag(sep_rate, default=0) = [0, sr[0], sr[1], ...]
        lagged_1 = np.zeros(m)
        lagged_1[1:] = sr[:-1]

        # lag(sep_rate, n=2, default=0) = [0, 0, sr[0], sr[1], ...]
        lagged_2 = np.zeros(m)
        if m > 2:
            lagged_2[2:] = sr[:-2]

        cum_surv = np.cumprod(1 - lagged_2)
        sep_prob = cum_surv * lagged_1

        value_adjusted = val * sep_prob

        if len(value_adjusted) > 1:
            PVFB[i] = npv(interest, value_adjusted[1:])

    return PVFB


def get_pvfs_r(remaining_prob_vec, interest, sal_vec):
    """
    Replicate R's get_pvfs function.

    R code (utility_functions.R lines 287-298):
    remaining_prob = remaining_prob / remaining_prob[1]  (normalize)
    PVFS[i] = npv(interest, sal_adjusted)
    """
    n = len(sal_vec)
    PVFS = np.zeros(n)

    for i in range(n):
        rp = remaining_prob_vec[i:].copy()
        if rp[0] > 0:
            rp = rp / rp[0]

        sal = sal_vec[i:]
        sal_adjusted = sal * rp

        PVFS[i] = npv(interest, sal_adjusted)

    return PVFS


def validate_single_cohort(entry_year, entry_age, r_data, sal_growth, params, cal):
    """Validate calculations for a single cohort against R data."""
    dr = params['dr_current'][0]
    cal_factor = cal['global_calibration']['cal_factor']
    payroll_growth = params['payroll_growth'][0]

    # Get R data for this cohort
    r_cohort = r_data[
        (r_data['entry_year'] == entry_year) &
        (r_data['entry_age'] == entry_age)
    ].sort_values('yos').reset_index(drop=True)

    if len(r_cohort) == 0:
        return None

    max_yos = len(r_cohort)

    # Step 1: Build salary from entry_salary and growth rates
    # Get R's entry salary (salary at yos=0)
    r_entry_salary = r_cohort.iloc[0]['salary']

    salary = build_salary_vector(entry_age, entry_year, r_entry_salary, sal_growth,
                                  payroll_growth, max_yos)

    # Step 2: Compute FAS
    fas_period = 5 if 'tier_1' in str(r_cohort.iloc[0]['tier_at_term_age']) else 8
    fas = compute_fas(salary, fas_period)

    # Step 3: Compute db_benefit
    db_benefit = np.zeros(max_yos)
    for i in range(max_yos):
        yos = r_cohort.iloc[i]['yos']
        age = r_cohort.iloc[i]['term_age']
        tier = str(r_cohort.iloc[i]['tier_at_term_age'])
        bm = get_benefit_multiplier(tier, yos, age)
        rf = get_reduce_factor(tier, age)
        if not np.isnan(fas[i]) and fas[i] > 0:
            db_benefit[i] = yos * bm * fas[i] * rf * cal_factor
        else:
            db_benefit[i] = 0.0

    # Compare salary, FAS, db_benefit
    results = {
        'entry_year': entry_year,
        'entry_age': entry_age,
        'n_yos': max_yos,
    }

    # Compare at a few YOS points
    for check_yos in [0, 10, 22, 30]:
        if check_yos >= max_yos:
            continue
        row = r_cohort.iloc[check_yos]

        py_sal = salary[check_yos]
        r_sal = row['salary']
        sal_diff = abs(py_sal - r_sal) / r_sal * 100 if r_sal > 0 else 0

        py_ben = db_benefit[check_yos]
        r_ben = row['db_benefit']
        ben_diff = abs(py_ben - r_ben) / r_ben * 100 if r_ben > 0 else 0

        results[f'sal_yos{check_yos}_py'] = py_sal
        results[f'sal_yos{check_yos}_r'] = r_sal
        results[f'sal_yos{check_yos}_diff%'] = sal_diff
        results[f'ben_yos{check_yos}_py'] = py_ben
        results[f'ben_yos{check_yos}_r'] = r_ben
        results[f'ben_yos{check_yos}_diff%'] = ben_diff

    return results


def validate_pvfb_pvfs(entry_year, entry_age, r_data, sal_growth, params, cal):
    """Validate PVFB and PVFS for a cohort using R's separation rates."""
    dr = params['dr_current'][0]
    cal_factor = cal['global_calibration']['cal_factor']
    payroll_growth = params['payroll_growth'][0]

    r_cohort = r_data[
        (r_data['entry_year'] == entry_year) &
        (r_data['entry_age'] == entry_age)
    ].sort_values('yos').reset_index(drop=True)

    if len(r_cohort) == 0:
        return None

    # Use R's own values for PVFB calculation inputs
    # (this validates our get_pvfb/get_pvfs implementations, not the inputs)
    sep_rates = r_cohort['separation_rate'].values
    remaining_prob = r_cohort['remaining_prob'].values
    pvfb_at_term = r_cohort['pvfb_db_wealth_at_term_age'].values
    salary = r_cohort['salary'].values

    # Calculate PVFB using our Python implementation of R's get_pvfb
    py_pvfb = get_pvfb_r(sep_rates, dr, pvfb_at_term)

    # Calculate PVFS using our Python implementation of R's get_pvfs
    py_pvfs = get_pvfs_r(remaining_prob, dr, salary)

    # Compare at entry (yos=0) and current (yos=22 for 2000/20 cohort)
    r_pvfb = r_cohort['pvfb_db_wealth_at_current_age'].values
    r_pvfs = r_cohort['pvfs_at_current_age'].values

    results = []
    for check_yos in [0, 10, 22]:
        if check_yos >= len(r_cohort):
            continue

        pvfb_diff = abs(py_pvfb[check_yos] - r_pvfb[check_yos]) / r_pvfb[check_yos] * 100 if r_pvfb[check_yos] > 0 else 0
        pvfs_diff = abs(py_pvfs[check_yos] - r_pvfs[check_yos]) / r_pvfs[check_yos] * 100 if r_pvfs[check_yos] > 0 else 0

        results.append({
            'yos': check_yos,
            'py_pvfb': py_pvfb[check_yos],
            'r_pvfb': r_pvfb[check_yos],
            'pvfb_diff%': pvfb_diff,
            'py_pvfs': py_pvfs[check_yos],
            'r_pvfs': r_pvfs[check_yos],
            'pvfs_diff%': pvfs_diff,
        })

    # NC rate comparison
    if py_pvfs[0] > 0:
        py_nc = py_pvfb[0] / py_pvfs[0]
    else:
        py_nc = 0
    r_nc = r_cohort.iloc[0]['indv_norm_cost']
    nc_diff = abs(py_nc - r_nc) / r_nc * 100 if r_nc > 0 else 0

    return results, py_nc, r_nc, nc_diff


def main():
    print("=" * 70)
    print("Cohort-Level Benefit Validation Against R Baseline")
    print("=" * 70)

    params, cal = load_params()
    sal_growth = pd.read_csv('baseline_outputs/salary_growth_table.csv')
    r_data = pd.read_csv('baseline_outputs/regular_benefit_data.csv')

    print(f"\nParameters: dr={params['dr_current'][0]}, cal_factor={cal['global_calibration']['cal_factor']}")
    print(f"R benefit data: {len(r_data):,} rows")

    # Test cohorts
    test_cohorts = [
        (2000, 20),   # Historical, young entrant
        (2000, 35),   # Historical, mid-career entrant
        (2010, 25),   # Near tier boundary
        (2015, 30),   # Tier 2
        (2020, 20),   # Recent entrant
    ]

    # Phase 1: Validate salary and db_benefit
    print(f"\n{'='*70}")
    print("PHASE 1: Salary and Benefit Calculation Validation")
    print(f"{'='*70}")

    for ey, ea in test_cohorts:
        result = validate_single_cohort(ey, ea, r_data, sal_growth, params, cal)
        if result is None:
            print(f"\n  Cohort ({ey}, {ea}): No R data")
            continue

        print(f"\n  Cohort (entry_year={ey}, entry_age={ea}):")
        for key, val in result.items():
            if 'diff%' in key:
                status = "OK" if val < 1.0 else "MISMATCH"
                print(f"    {key}: {val:.2f}% [{status}]")
            elif key.startswith('sal_') or key.startswith('ben_'):
                print(f"    {key}: {val:,.2f}")

    # Phase 2: Validate PVFB and PVFS (using R's own inputs)
    print(f"\n{'='*70}")
    print("PHASE 2: PVFB/PVFS Calculation Validation")
    print("(Using R's separation rates and pension wealth as inputs)")
    print(f"{'='*70}")

    for ey, ea in test_cohorts:
        result = validate_pvfb_pvfs(ey, ea, r_data, sal_growth, params, cal)
        if result is None:
            print(f"\n  Cohort ({ey}, {ea}): No R data")
            continue

        pvfb_results, py_nc, r_nc, nc_diff = result

        print(f"\n  Cohort (entry_year={ey}, entry_age={ea}):")
        for r in pvfb_results:
            pvfb_status = "OK" if r['pvfb_diff%'] < 1.0 else "MISMATCH"
            pvfs_status = "OK" if r['pvfs_diff%'] < 1.0 else "MISMATCH"
            print(f"    YOS={r['yos']:2d}: PVFB py={r['py_pvfb']:>12,.0f} r={r['r_pvfb']:>12,.0f} diff={r['pvfb_diff%']:.2f}% [{pvfb_status}]")
            print(f"           PVFS py={r['py_pvfs']:>12,.0f} r={r['r_pvfs']:>12,.0f} diff={r['pvfs_diff%']:.2f}% [{pvfs_status}]")

        nc_status = "OK" if nc_diff < 1.0 else "MISMATCH"
        print(f"    NC rate: py={py_nc:.6f} r={r_nc:.6f} diff={nc_diff:.2f}% [{nc_status}]")


if __name__ == "__main__":
    main()
