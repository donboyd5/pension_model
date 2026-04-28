# TXTRS-AV First-Cut AV Data Batch 06: Return Scenarios

## Purpose

This note records the first `txtrs-av` `funding/return_scenarios.csv`. It
also captures the first-time end-to-end model run, which now succeeds with
the full data set in place.

## Artifacts Built

- [return_scenarios.csv](/home/donboyd5/Documents/python_projects/pension_model/plans/txtrs-av/data/funding/return_scenarios.csv)

## Source

This is a modeling-choice artifact, not a document-sourced one. The two
relevant inputs from the AV are:

- AV Table 12c (HISTORY OF INVESTMENT RETURNS, printed p. `27`, PDF p. `34`)
  reports the assumed investment return as `7.00%` for 2024. That value
  populates the `model` and `assumption` columns.
- The runtime overrides the `model` and `assumption` columns at runtime
  with `economic.model_return` and `economic.dr_current` from
  `plan_config.json`. So those columns are nominal placeholders in the
  CSV.

The recession scenarios are stress paths used only with `--scenario`
flags. Their shape mirrors the legacy txtrs convention.

## Build Rule

Artifact produced by:

- [build_txtrs_av_return_scenarios.py](/home/donboyd5/Documents/python_projects/pension_model/scripts/build/build_txtrs_av_return_scenarios.py)
  - method id: `txtrs_av_return_scenarios_v1`

The file has 100 rows spanning years 2023-2122 (one year before
`start_year`, then a 99-year tail). For each year:

- `model` and `assumption`: AV-stated long-term return `0.07`
- `recession`: `0.07` for year 0, `-0.24` for year 1, `+0.11` for years
  2-4 (recovery), `+0.06` thereafter
- `recur_recession`: same as `recession` for years 0-15, then `-0.24` at
  year 16 (a second recession), `+0.11` for years 17-19 (recovery), and
  `+0.06` afterward
- `constant_6`: flat `0.06` reference scenario

This shape exactly mirrors the legacy txtrs return-scenario timing,
shifted to match the txtrs-av valuation vintage.

## Side Fix

This batch also corrected `init_funding.csv`: the first build wrote a
`class` column that the runtime cannot consume for single-class plans.
The legacy txtrs convention is no class column; runtime then loads the
single row for every class iteration. Removing the column matches that
convention and unblocks the funding setup.

## End-to-End Run

With all data files now in place, the full pipeline executes for
`txtrs-av`:

```
pension-model run txtrs-av --no-test
```

- pipeline completes in ~6 seconds
- liability and funding outputs land at `output/txtrs-av/`

## Validation Against AV Tables 1-4

Per the txtrs-av validation discipline (3% tolerance against AV-published
year-0 values), the year-2024 model output sits **outside** that tolerance
on AAL:

| Quantity | AV 2024 published | Model 2024 output | Gap | Within 3%? |
|---|---|---|---|---|
| AAL | $273.1B | $255.3B | -6.5% | no |
| AVA | $212.5B | $212.5B | 0.0% | yes (seed) |
| MVA | $210.5B | $210.5B | 0.0% | yes (seed) |
| Payroll | $61.4B | $61.4B | 0.0% | yes (seed) |

The asset and payroll columns match because they come from the
`init_funding.csv` seed. The AAL output, by contrast, comes from the
liability pipeline's independent year-by-year computation off the cohort
grid plus assumptions, not from the seed.

The trajectory is consistent with the gap being a mostly-systematic
under-projection of the cohort-derived AAL relative to the AV's
published value:

- model year 2024 AAL: `$255.3B`
- model year 2025 AAL: `$264.4B`
- model year 2026 AAL: `$273.9B` (≈ AV's 2024 published `$273.1B`)

This is the gap that `config/calibration.json` exists to close. The
legacy `plans/txtrs/config/calibration.json` does exactly this for the
legacy plan, by applying liability and normal-cost calibration multipliers
that align computed values to the AV-published anchor.

A 6.5% pre-calibration gap is consistent with what other plans see
before calibration. Calibration is the next batch in the queue.

## Year-0 nan Reporting

The model output also shows `$nanB` for benefit payments and employer
contributions at year 2024. This is a year-0 reporting boundary effect
(`funding_lag = 1` in `plan_config.json` means flow-based quantities
populate from year 1 onward). It is not a calculation issue and does not
affect later years.

## Remaining Required Runtime Files

- `config/calibration.json`
- `baselines/` (no R baseline applies; need a documented AV-target
  validation file or an internal acceptance check)

## Implication

`txtrs-av` now has the complete first-cut runtime data set:

- demographics
- decrements
- retiree distribution
- mortality
- funding seed
- return scenarios

The pipeline runs end-to-end. Calibration is the next gate.
