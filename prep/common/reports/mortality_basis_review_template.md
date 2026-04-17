# Mortality Basis Review Template

## Purpose

Use this template when reviewing whether a plan's mortality inputs are:

- source-faithful to the valuation's stated mortality basis
- merely compatible with the current reviewed runtime files
- or blocked by missing sources or ambiguous implementation rules

This review is intentionally dual-track:

1. can we reproduce the current runtime mortality artifacts?
2. can we reconstruct the valuation's stated mortality basis?

Those two answers may differ.

## Plan And Source Context

- Plan:
- Valuation report used:
- Other mortality-related documents used:
- Shared external references used:
- Missing external references:

## 1. Source-Stated Mortality Basis

Record the valuation's narrative exactly enough for implementation.

| Member state | Stated basis | Projection scale | Special adjustments | Source location | Notes |
| --- | --- | --- | --- | --- | --- |
| active |  |  |  |  |  |
| healthy retiree |  |  |  |  |  |
| disabled retiree |  |  |  |  |  |
| other |  |  |  |  |  |

## 2. Runtime Mortality Representation

Document the current runtime contract and artifacts.

| Runtime item | Current value / structure | Location | Notes |
| --- | --- | --- | --- |
| plan config base table |  |  |  |
| plan config improvement scale |  |  |  |
| sex handling |  |  |  |
| employee / retiree distinction |  |  |  |
| disabled-retiree handling |  |  |  |
| other |  |  |  |

## 3. External Source Inventory

List both present and missing external source files.

| Source file / table | Present? | Provenance known? | Used by current runtime? | Needed for source-faithful build? | Notes |
| --- | --- | --- | --- | --- | --- |
| shared SOA base table |  |  |  |  |  |
| shared improvement scale |  |  |  |  |  |
| plan-specific retiree table |  |  |  |  |  |
| plan-specific technical note |  |  |  |  |  |

## 4. Implementation Rules To Confirm

Mortality gaps are often not just missing files. Record the implementation
rules that may still be ambiguous.

| Question | Current understanding | Evidence | Status | Notes |
| --- | --- | --- | --- | --- |
| male/female set forward |  |  |  |  |
| immediate convergence |  |  |  |  |
| ultimate-rate handling |  |  |  |  |
| disabled-retiree floor timing |  |  |  |  |
| sex aggregation in runtime |  |  |  |  |
| other |  |  |  |  |

## 5. Sample-Rate Comparison

When the valuation publishes specimen rates, compare them to the resolved
runtime rates.

| Member state | Year | Age | Valuation sample | Runtime resolved rate | Difference | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| active |  |  |  |  |  |  |
| retiree |  |  |  |  |  |  |
| disabled retiree |  |  |  |  |  |  |

## 6. Alignment Assessment

Answer separately:

### A. Runtime reproducibility

- `yes`
- `partial`
- `no`

Notes:

### B. Source-faithful reconstruction of the valuation basis

- `yes`
- `partial`
- `no`

Notes:

## 7. Classification

Choose one:

- `source-faithful`
- `source-faithful for active only`
- `compatibility approximation`
- `blocked by missing source`
- `blocked by implementation ambiguity`
- `blocked by both missing source and implementation ambiguity`

## 8. Decision / Next Step

Choose one:

- `keep current runtime as compatibility path only`
- `acquire missing external source`
- `confirm implementation rule`
- `revise runtime contract semantics`
- `ready for source-faithful rebuild`

Decision notes:

## 9. Related Artifacts

- mortality mapping note:
- external-source requirements note:
- issue links:

