# Artifact Coverage Matrix Template

## Purpose

Use this template for the artifact-level mapping between the current runtime
contract and the plan's likely source basis.

This is not a field-level lineage table. The goal is to answer:

```text
For each runtime artifact under plans/{plan}, what is the likely source basis,
how directly is it available, and what kind of prep work will be needed?
```

## Primary References

- actuarial valuation:
- AV-referenced external sources:
- auxiliary estimation-support sources:
- narrative analysis:
- source sufficiency summary:

## Status Legend

- `direct_from_av`
- `direct_from_av_referenced_external`
- `derived_from_av`
- `estimation_supported`
- `referenced_not_published`
- `runtime_only`
- `computed`
- `missing`

## Config Artifacts

| Runtime artifact | Status | Likely primary source(s) | Notes |
| --- | --- | --- | --- |
| `plans/{plan}/config/plan_config.json` |  |  |  |
| `plans/{plan}/config/calibration.json` |  |  |  |

## Demographics Artifacts

| Runtime artifact | Status | Likely primary source(s) | Notes |
| --- | --- | --- | --- |
| `plans/{plan}/data/demographics/...` |  |  |  |

## Decrement Artifacts

| Runtime artifact | Status | Likely primary source(s) | Notes |
| --- | --- | --- | --- |
| `plans/{plan}/data/decrements/...` |  |  |  |

## Funding Artifacts

| Runtime artifact | Status | Likely primary source(s) | Notes |
| --- | --- | --- | --- |
| `plans/{plan}/data/funding/...` |  |  |  |

## Mortality Artifacts

| Runtime artifact | Status | Likely primary source(s) | Notes |
| --- | --- | --- | --- |
| `plans/{plan}/data/mortality/...` |  |  |  |

## Main Coverage Conclusions

-

## Next Field-Level Follow-Up

For the highest-value artifacts, the next pass should map critical fields or
field groups to:

- source document ID
- printed page
- PDF page
- table or section label
- source unit
- canonical unit
- transform rule
- provenance type
