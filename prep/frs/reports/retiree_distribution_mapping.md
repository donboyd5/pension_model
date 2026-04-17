# FRS Retiree Distribution Mapping Notes

## Purpose

This note records the current understanding of how the FRS runtime
`retiree_distribution.csv` relates to published plan documents and to the
retained Reason workbook.

## Current Runtime Artifact

Current canonical file:

- [plans/frs/data/demographics/retiree_distribution.csv](/home/donboyd5/Documents/python_projects/pension_model/plans/frs/data/demographics/retiree_distribution.csv)

The runtime artifact is an age-by-age table with:

- `age`
- `count`
- `avg_benefit`
- `total_benefit`

The shape is visibly smoothed:

- ages within five-year bands repeat the same `count` and `total_benefit`
- ages within older ten-year bands also repeat the same values
- some of the oldest ages are flat-carried from the previous row

So the runtime artifact is clearly not a direct one-row-per-age extraction from
the valuation PDF.

## Published Source Information

Primary source:

- [Florida FRS Valuation 2022.pdf](/home/donboyd5/Documents/python_projects/pension_model/prep/frs/sources/Florida%20FRS%20Valuation%202022.pdf)
  - printed page `C-2`, PDF page `94`
  - `Table C-1` `Annuitants at July 1, 2022 Regular and Early Retirement by Age`
  - `Table C-2` `Disability Retirement by Age`

Those two grouped age tables publish the exact literals that appear in the
Reason workbook formulas.

Examples:

- `Under 50`
  - Table C-1: `1,964` and `$28,474` thousand
  - Table C-2: `424` and `$8,740` thousand
- `50 to 54`
  - Table C-1: `3,903` and `$133,928` thousand
  - Table C-2: `805` and `$15,834` thousand
- `55 to 59`
  - Table C-1: `15,381` and `$520,884` thousand
  - Table C-2: `1,663` and `$33,505` thousand
- `60 to 64`
  - Table C-1: `46,187` and `$1,231,948` thousand
  - Table C-2: `2,471` and `$43,097` thousand
- `80 & Up`
  - Table C-1: `87,072` and `$2,125,387` thousand
  - Table C-2: `1,033` and `$17,878` thousand

## What The Reason Workbook Does

Retained workbook:

- [R_model/R_model_frs/Florida FRS inputs.xlsx](/home/donboyd5/Documents/python_projects/pension_model/R_model/R_model_frs/Florida%20FRS%20inputs.xlsx)
  - `Retiree Distribution` sheet

The workbook builds a single-age distribution by smoothing those grouped
valuation totals across age ranges.

Examples:

- age `45`:
  - `n_retire = (1964 + 424) / 5`
  - `total_ben = (28,474,000 + 8,740,000) / 5`
- age `53`:
  - `n_retire = (3903 + 805) / 5`
  - `total_ben = (133,928,000 + 15,834,000) / 5`
- age `58`:
  - `n_retire = (15381 + 1663) / 5`
  - `total_ben = (520,884,000 + 33,505,000) / 5`
- age `63`:
  - `n_retire = (46187 + 2471) / 5`
  - `total_ben = (1,231,948,000 + 43,097,000) / 5`
- age `83`:
  - `n_retire = (87,072 + 1,033) / 10`
  - `total_ben = (2,125,387,000 + 17,878,000) / 10`

The workbook then computes:

- `avg_ben = total_ben / n_retire`
- `n_retire_ratio`
- `total_ben_ratio`

## Current Working Interpretation

The correct classification is now:

- grouped source totals are published directly in the valuation
- the runtime age distribution is `derived`
- the retained workbook provides a legacy smoothing rule
- the unresolved part is no longer the grouped inputs
- the unresolved part is whether the smoothing rule itself is a reviewed
  canonical step or only a Reason-era intermediate convenience

This is better than the previous understanding, which treated the grouped
workbook literals as possibly unexplained.

## What Is Resolved

- the runtime file is not a direct transcription of a published age table
- the workbook uses explicit five-year and ten-year spreading logic
- the grouped counts and grouped benefit totals used in that logic come
  directly from valuation Appendix C tables
- the workbook `Retiree Distribution` sheet is a substantive intermediate
  artifact, not a passive copy

## What Is Not Yet Resolved

- why the smoothing starts at the specific single ages used in the workbook
- whether the oldest-age flat-carry rules were deliberate and reviewed
- whether the current runtime artifact matches the workbook exactly or reflects
  later adjustments
- whether this smoothing rule should remain a legacy reconstruction note or be
  generalized later into a documented prep method

## Practical Implication For Prep

For FRS retiree distribution, the source-to-runtime path is now much clearer:

1. valuation Appendix C grouped retiree and disability tables
2. workbook smoothing to single ages
3. runtime age-by-age distribution artifact

So the remaining prep question is not where the grouped values came from. It is
how we should treat the smoothing step:

- as a legacy reconstruction rule needed to reproduce current stage-3 exactly
- or, later, as a deliberate documented estimation / canonicalization method

