# TXTRS-AV First-Cut AV Data Batch 01

## Purpose

This note records the first runtime data artifacts built for `txtrs-av`
directly from the local 2024 valuation PDF.

The goal of this batch was to add only source-strong artifacts whose build
rules are now understood well enough to support AV-first onboarding without
carrying files in directly from `txtrs`.

## Artifacts Built

- [all_headcount.csv](/home/donboyd5/Documents/python_projects/pension_model/plans/txtrs-av/data/demographics/all_headcount.csv)
- [all_salary.csv](/home/donboyd5/Documents/python_projects/pension_model/plans/txtrs-av/data/demographics/all_salary.csv)
- [entrant_profile.csv](/home/donboyd5/Documents/python_projects/pension_model/plans/txtrs-av/data/demographics/entrant_profile.csv)
- [salary_growth.csv](/home/donboyd5/Documents/python_projects/pension_model/plans/txtrs-av/data/demographics/salary_growth.csv)
- [reduction_gft.csv](/home/donboyd5/Documents/python_projects/pension_model/plans/txtrs-av/data/decrements/reduction_gft.csv)
- [reduction_others.csv](/home/donboyd5/Documents/python_projects/pension_model/plans/txtrs-av/data/decrements/reduction_others.csv)

## Source Pages Used

- Table 17 active-member grid:
  - printed page `41`
  - PDF page `48`
- Appendix 2 salary increase assumptions:
  - printed page `63`
  - PDF page `70`
- Appendix 2 new entrant profile:
  - printed page `69`
  - PDF page `76`
- Appendix 1 early-retirement reduction tables:
  - printed page `47`
  - PDF page `54`

## Build Path

Artifacts in this batch are produced by:

- [build_txtrs_av_from_av.py](/home/donboyd5/Documents/python_projects/pension_model/scripts/build/build_txtrs_av_from_av.py)

The script uses:

- local valuation PDF only
- `pdftotext -layout`
- txtrs-av-specific parsing and normalization rules

It does **not** read `plans/txtrs/**` artifacts as inputs.

## Validation Status

For five of the six artifacts in this batch, the AV-derived outputs match the
reviewed `txtrs` runtime artifacts exactly:

- active headcount
- active salary
- entrant profile
- grandfathered reduction table
- other-members reduction table

For salary growth:

- the AV-derived values match the reviewed runtime values over the shared range
- `txtrs-av` currently carries the flat `25 & up` rate only through its current
  configured `max_yos` horizon
- the older `txtrs` artifact extends that flat tail farther as a longer runtime
  convenience

That difference is a horizon choice, not a source-content difference.

## What Remains Missing

After this batch, the remaining required runtime files are:

- `demographics/retiree_distribution.csv`
- `decrements/all_termination_rates.csv`
- `decrements/all_retirement_rates.csv`
- `mortality/base_rates.csv`
- `mortality/improvement_scale.csv`
- `funding/init_funding.csv`
- `funding/return_scenarios.csv`

## Implication

`txtrs-av` now has a real AV-built first data batch.

The next source-approved targets should be:

1. retirement and termination tables
2. funding seed file
3. mortality files
4. retiree distribution
