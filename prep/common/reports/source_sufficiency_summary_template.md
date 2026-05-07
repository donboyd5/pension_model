# Source Sufficiency Summary Template

## Purpose

Use this template for the first category-level pass on whether a plan's source
documents can support the current runtime input contract.

This is intentionally broader than field-level lineage. The goal is to answer:

```text
Given the current runtime contract, what appears recoverable from the AV,
what appears recoverable only with AV-referenced external materials,
what may require estimation support from other documents,
and what is still missing?
```

## Source Hierarchy Reminder

For new plans:

- the AV is the source document
- external sources explicitly named in the AV are part of the authoritative
  source set for the governed item
- ACFR and similar documents are aids in estimation, reconciliation, or
  clue-mining unless a plan-specific review justifies a stronger role

## Primary Sources

- actuarial valuation:
- AV-referenced external sources:
- auxiliary estimation-support sources:
- runtime-contract reference:

## Status Legend

- `direct_from_av`: reported in the AV in a form close to runtime needs
- `direct_from_av_referenced_external`: supplied by an external table or
  standard explicitly named by the AV
- `derived_from_av`: available from the AV after transformation, regrouping, or
  scaling
- `estimation_supported`: not direct from the AV, but potentially supportable
  through estimation using auxiliary documents
- `referenced_not_published`: the AV identifies the concept or basis, but does
  not publish the full canonical values
- `runtime_only`: needed by the runtime but not document-sourced
- `computed`: produced by procedure rather than sourced from documents
- `missing`: not currently recoverable from the identified sources

## First-Pass Assessment

| Runtime input area | First-pass status | Notes |
| --- | --- | --- |
| plan structure, classes, tiers |  |  |
| benefit formulas, vesting, NRA, early retirement, COLA, DROP rules |  |  |
| active headcount |  |  |
| active salary |  |  |
| salary growth assumptions |  |  |
| retiree distribution |  |  |
| entrant profile |  |  |
| retirement assumptions |  |  |
| termination assumptions |  |  |
| early-retirement reduction tables or rules |  |  |
| mortality basis names and mappings |  |  |
| mortality base-rate values |  |  |
| mortality improvement-scale values |  |  |
| funding seed values for `init_funding.csv` |  |  |
| amortization-layer support |  |  |
| source-linked portions of `plan_config.json` |  |  |
| runtime-only settings |  |  |
| calibration |  |  |

## Main Observations

-

## Main Risks For Source-To-Canonical Prep

-

## Next Step

The next pass should be an artifact-level coverage matrix that maps each
runtime artifact to likely source basis, prep status, and major build needs.
