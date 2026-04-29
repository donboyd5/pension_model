# TXTRS Entrant Profile Mapping Notes

## Purpose

This note records the current understanding of the TXTRS entrant-profile source
and how it relates to the current runtime artifact.

## Source Found In The Valuation

Source:

- [Texas TRS Valuation 2024.pdf](/home/donboyd5/Documents/python_projects/pension_model/prep/txtrs/sources/Texas%20TRS%20Valuation%202024.pdf)
  - Appendix 2, printed p. 68

The valuation includes a section titled:

- `NEW ENTRANT PROFILE`

And publishes a summary table with:

- entry-age bands
- number of employees
- average salary

The table is explicitly described as the basis for the open-group projection
used in the funding-period calculation.

## What The Valuation Publishes

Published summary rows include:

- `15-19` with `859` employees and average salary `$25,003`
- `20-24` with `49,665` employees and average salary `$47,410`
- `25-29` with `85,761` employees and average salary `$51,659`
- ...
- `65-69` with `2,372` employees and average salary `$39,321`
- total `393,267` employees and overall average salary `$49,694`

The valuation also says:

- the profile is created from valuation data using members with eight or less
  years of service
- salaries are normalized to the valuation date
- 25.9% of the population is male
- future new-hire salaries grow at general wage inflation of 2.90%

## How This Compares To The Current Runtime Artifact

Current runtime artifact:

- [plans/txtrs/data/demographics/entrant_profile.csv](/home/donboyd5/Documents/python_projects/pension_model/plans/txtrs/data/demographics/entrant_profile.csv)

Current canonical columns:

- `entry_age`
- `start_salary`
- `entrant_dist`

The current runtime file is **not** a direct transcription of the valuation
summary table.

Examples:

- runtime uses single ages such as `20`, `25`, `30`, ... rather than age bands
- runtime distributions do not match a simple normalization of the published
  age-band counts
- runtime start salaries do not match the published band-average salaries
  one-for-one

## Exact Build Rule Now Verified

The current runtime artifact can now be reproduced exactly from the valuation
table.

Verified against:

- [plans/txtrs/data/demographics/entrant_profile.csv](/home/donboyd5/Documents/python_projects/pension_model/plans/txtrs/data/demographics/entrant_profile.csv)

Exact rule:

- canonical entry ages are:
  - `20, 25, 30, 35, 40, 45, 50, 55, 60, 65`
- count mapping:
  - `20` uses `15-19 + 20-24`
  - `25` uses `20-24`
  - `30` uses `25-29`
  - `35` uses `30-34`
  - `40` uses `35-39`
  - `45` uses `40-44`
  - `50` uses `45-49`
  - `55` uses `50-54`
  - `60` uses `55-59`
  - `65` uses `60-64 + 65-69`
- start-salary mapping:
  - each canonical age uses the simple average of the two adjacent valuation
    band-average salaries
  - examples:
    - `20 -> average(15-19 salary, 20-24 salary)`
    - `25 -> average(20-24 salary, 25-29 salary)`
    - ...
    - `65 -> average(60-64 salary, 65-69 salary)`
- `entrant_dist` is each canonical count divided by the total canonical count

Verification result:

- runtime rows: `10`
- missing rows: `0`
- extra rows: `0`
- start-salary mismatches: `0`
- entrant-distribution mismatches: `0`

This means the workbook `Entrant Profile` tab is not a richer hidden source.
It is an exact intermediate representation of a transformation that can already
be reconstructed from the valuation PDF alone.

## Current Working Interpretation

The correct classification is now:

- source exists in the PDF
- runtime artifact is `derived`
- exact reviewed build rule is known

## Implication For Prep

For TXTRS, `entrant_profile.csv` is now a clean source-grounded build artifact.

The prep path is:

- extract the valuation `NEW ENTRANT PROFILE` table
- apply the reviewed boundary-merge and adjacent-band-average rule above
- normalize counts to `entrant_dist`
- validate exact equality to the canonical runtime file
