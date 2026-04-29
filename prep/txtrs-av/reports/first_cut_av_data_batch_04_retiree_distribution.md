# TXTRS-AV First-Cut AV Data Batch 04: Retiree Distribution

## Purpose

This note records the first `txtrs-av` retiree age distribution built directly
from the local 2024 valuation PDF.

The runtime artifact is an age-by-age table that the funding pipeline uses to
project benefit payments forward against retiree mortality.

## Artifacts Built

- [retiree_distribution.csv](/home/donboyd5/Documents/python_projects/pension_model/plans/txtrs-av/data/demographics/retiree_distribution.csv)

## Source

- AV `Distribution of Life Annuities by Age` (Table 18)
  - printed page `42`
  - PDF page `49`

The table publishes 15 age bands. Each band has a published count, annual
annuity total, and monthly average annuity. The published Total row is
`475,891` retirees and `$13,100,519,264` of annual annuities.

## Build Rule

Artifact produced by:

- [build_txtrs_av_from_av.py](/home/donboyd5/Documents/python_projects/pension_model/scripts/build/build_txtrs_av_from_av.py)
  - method id: `retiree_distribution_av18_band_spread_v1`

Logic:

- read the 15 published bands directly from the PDF
- validate the parsed counts and annuities sum to the published Total row
- aggregate the five pre-retirement bands (`Up to 35`, `35-40`, `40-44`,
  `45-49`, `50-54`) and the `55-59` band into a single runtime band covering
  ages 55-59, because the runtime age axis starts at 55
- spread each later 5-year band evenly across its five runtime ages
- spread the published `100 & up` band evenly across runtime ages 100-120
- per runtime age write `count = band_count / n_ages`,
  `total_benefit = band_annual / n_ages`, and
  `avg_benefit = band_annual / band_count` (constant within a band)

This produces the canonical four-column runtime artifact with rows for ages
55 through 120.

## Scope Notes

The first-cut artifact uses life annuities only.

The AV publishes age distributions for two groups:

- Table 18 life annuities: `475,891` retirees / `$13.10B` annual
- Table 19 disabled annuities: `12,030` retirees / `$0.19B` annual

Other benefit-receiving groups reported in Table 15b but not published with an
age distribution:

- annuities certain: `2,392` persons / `$0.04B` annual
- survivor annuities (currently in pay): `17,433` persons / `$0.05B` annual
- survivor annuities (deferred): `858` persons / `$0.003B` annual

So Table 18 alone covers about `93.5%` of the published `508,701` benefit
recipients and about `97.9%` of the published `$13.39B` annual annuities.

The remaining groups are excluded from this first cut as a documented
modeling simplification:

- disabled annuitants have a published age distribution and could be folded in
  cleanly using the same band-spread method, but they have meaningfully
  different mortality and arguably need a separate table; they are deferred
  pending the runtime decision on whether to support a separate disabled
  cohort or to merge them into one retiree table
- survivor and annuities-certain groups are not published age-by-age; they
  would require either an estimation method or a documented approximation to
  fold them in

These choices are tracked as candidate future inclusions, not permanent
exclusions. See issue #71.

## Cross-Check Against Reviewed `txtrs` Artifact

The reviewed `plans/txtrs/data/demographics/retiree_distribution.csv` artifact
is built from the same AV Table 18 with the same method.

Independent build of `txtrs-av` from the AV PDF reproduces the reviewed
artifact at floating-point precision:

- counts match exactly per row
- total benefits match exactly per row
- average benefits match within last-digit float representation noise

This is an equality cross-check, not source inheritance: `txtrs-av` is built
from the AV directly via the documented method, and the agreement is evidence
that the legacy reviewed file is itself source-faithful.

## Remaining Required Runtime Files

- `mortality/base_rates.csv`
- `mortality/improvement_scale.csv`
- `funding/return_scenarios.csv`

## Implication

`txtrs-av` now has an AV-built retiree distribution.

The next source-strong target is mortality, where the AV names Pub-2010 plus
an MP-scale projection and the SOA workbooks supply the rates.
