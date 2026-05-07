# TXTRS-AV First-Cut AV Data Batch 03: Retirement and Termination Assumptions

## Purpose

This note records the first `txtrs-av` decrement tables built directly from the
local 2024 valuation PDF.

The goal is to add the published retirement and termination assumptions in a
runtime shape that preserves actuarial structure rather than carrying in the
older `txtrs` runtime files.

## Artifacts Built

- [all_retirement_rates.csv](/home/donboyd5/Documents/python_projects/pension_model/plans/txtrs-av/data/decrements/all_retirement_rates.csv)
- [all_termination_rates.csv](/home/donboyd5/Documents/python_projects/pension_model/plans/txtrs-av/data/decrements/all_termination_rates.csv)

## Source Pages Used

- Appendix 2 `Rates of Termination`
  - printed page `61`
  - PDF page `68`
- Appendix 2 `Rates of Retirement`
  - printed page `62`
  - PDF page `69`
- Appendix 2 retirement adjustment narrative
  - printed page `63`
  - PDF page `70`

## Build Rule

Artifacts in this batch are produced by:

- [build_txtrs_av_from_av.py](/home/donboyd5/Documents/python_projects/pension_model/scripts/build/build_txtrs_av_from_av.py)

### Termination

The valuation publishes a TRS-style select-and-ultimate structure:

- service years `1` to `10`
- then years from normal retirement `1` to `32`

The runtime file preserves that structure:

- source service year `1..10` maps to runtime `lookup_type = yos` with
  `lookup_value = 0..9`
- source years-from-NR `1..32` maps to runtime `lookup_type = years_from_nr`
  with `lookup_value = 1..32`
- an explicit runtime row `years_from_nr = 0, term_rate = 0` is added because
  the separation builder clips negative values to zero and benefits from an
  exact zero-year lookup

This keeps the assumption in its published actuarial form rather than
pre-expanding by cohort.

### Retirement

The valuation publishes:

- normal retirement rates by age and sex
- early retirement rates by age
- narrative cohort-specific rate increases for certain post-2007 members once
  they are beyond Rule of 80 but not yet at the relevant minimum unreduced
  retirement age

The current TRS-style runtime path takes a single age-based normal-retirement
schedule, not separate male and female schedules. So this first-cut build uses:

- `normal retire rate = (male + female) / 2`

by published age.

Other normalization rules:

- ages below published retirement ages are zero-filled
- the `65-69` and `70-74` bands are expanded to single ages
- `75+ = 1.0` is carried through the `txtrs-av` max-age horizon
- `tier = all` because the current years-from-NR separation builder uses one
  published retirement schedule and applies tier effects through runtime
  eligibility logic in config

## Scope Notes

This batch preserves the published actuarial structure as closely as the
current runtime contract allows.

The main normalization choice is the averaging of male and female normal
retirement rates. That is a runtime-shape concession, not a source claim that
TRS itself used sex-averaged normal retirement assumptions.

The narrative cohort-specific retirement-rate increases are not stored as extra
CSV rows here; they remain in the runtime tier logic driven by
[plan_config.json](/home/donboyd5/Documents/python_projects/pension_model/plans/txtrs-av/config/plan_config.json).

## Remaining Required Runtime Files

- `demographics/retiree_distribution.csv`
- `mortality/base_rates.csv`
- `mortality/improvement_scale.csv`
- `funding/return_scenarios.csv`

## Implication

`txtrs-av` now has AV-built retirement and termination assumption files.

The next source-strong targets are:

1. mortality files
2. retiree distribution
3. return scenarios
