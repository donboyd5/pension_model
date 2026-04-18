# TXTRS-AV Launch Assessment

## Purpose

This note answers a practical question:

- is the repo ready to start `txtrs-av` as a fresh AV-first onboarding of Texas
  TRS?

`txtrs-av` is not a brand-new plan type. It is a fresh source-first build of a
plan with the same broad actuarial shape as the current `txtrs` runtime path.
So the relevant standard is not "can the repo support any imaginable third
plan?" but:

- can the repo support a controlled first-cut onboarding of a new
  `plans/txtrs-av/` variant using the shared intake package and only
  data/config work?

## Current Conclusion

Short answer:

- yes, for a controlled first cut

More precisely:

- the repo is ready to start `txtrs-av` now if we treat it as a cautious
  AV-first intake
- the first cut should stay simple and source-faithful
- the first cut should not promise full source-faithful replacement of every
  current `txtrs` compatibility artifact on day one

## Why `txtrs-av` Is Feasible Now

### 1. Shared new-plan foundations are in place

The shared readiness package now exists and is usable:

- runtime target under `plans/{plan}/` is documented
- shared intake templates exist
- source-role and provenance scaffolding exist
- shared checks exist
- reusable versus legacy-only methods are now separated

See:

- [prep/common/reports/new_plan_readiness_checklist.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/new_plan_readiness_checklist.md)
- [prep/common/reports/new_plan_readiness_status.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/new_plan_readiness_status.md)
- [docs/runtime_input_contract.md](/home/donboyd5/Documents/python_projects/pension_model/docs/runtime_input_contract.md)

### 2. The runtime can host another TXTRS-shaped plan folder

The runtime and CLI already discover plans from `plans/*/config/plan_config.json`.

That means `txtrs-av` does not need a code registry or branch-specific loader
change just to exist as a separate plan folder.

### 3. Several important TXTRS source-to-runtime paths are already strong

Current TXTRS prep work shows that the following are already in good shape for a
fresh AV-first build:

- valuation-scoped `valuation_inputs` are directly anchored to the 2024 AV
- active headcount and salary grid have an exact PDF-to-canonical transform
- entrant profile has an exact PDF-to-canonical transform
- broad plan structure, tiering, eligibility, and reduction logic are strongly
  described by the AV

See:

- [prep/txtrs/reports/selected_field_lineage.md](/home/donboyd5/Documents/python_projects/pension_model/prep/txtrs/reports/selected_field_lineage.md)
- [prep/txtrs/reports/active_grid_mapping.md](/home/donboyd5/Documents/python_projects/pension_model/prep/txtrs/reports/active_grid_mapping.md)
- [prep/txtrs/reports/entrant_profile_mapping.md](/home/donboyd5/Documents/python_projects/pension_model/prep/txtrs/reports/entrant_profile_mapping.md)
- [prep/txtrs/reports/valuation_input_scope.md](/home/donboyd5/Documents/python_projects/pension_model/prep/txtrs/reports/valuation_input_scope.md)

## What `txtrs-av` Should Not Assume Yet

The repo is ready for a first cut, not for a claim that every current TXTRS
artifact already has a clean source-faithful path.

### 1. Retiree mortality is still a real source gap

The valuation names a plan-specific retiree mortality basis:

- `2021 TRS of Texas Healthy Pensioner Mortality Tables`
- `Scale UMP 2021`

That basis is not fully in hand in the repo today, and the current runtime
mortality path is still compatibility-oriented.

See:

- [prep/txtrs/reports/mortality_mapping.md](/home/donboyd5/Documents/python_projects/pension_model/prep/txtrs/reports/mortality_mapping.md)
- [prep/txtrs/reports/external_source_requirements.md](/home/donboyd5/Documents/python_projects/pension_model/prep/txtrs/reports/external_source_requirements.md)
- GitHub issue [#52](https://github.com/donboyd5/pension_model/issues/52)

### 2. Retiree distribution is still legacy-workbook-mediated

The current age-by-age retiree distribution still appears to come through a
workbook smoothing path whose grouped upstream source values are not yet pinned
down cleanly from plan documents alone.

See:

- [prep/txtrs/reports/retiree_distribution_mapping.md](/home/donboyd5/Documents/python_projects/pension_model/prep/txtrs/reports/retiree_distribution_mapping.md)
- GitHub issues [#53](https://github.com/donboyd5/pension_model/issues/53) and [#54](https://github.com/donboyd5/pension_model/issues/54)

### 3. Some current TXTRS config semantics are runtime-oriented, not source-direct

Current prep notes already classify some items as `runtime_only`, especially the
current `benefit_types` mix. That does not block `txtrs-av`, but it means the
new first cut should make those scope choices explicit instead of inheriting
them silently from `txtrs`.

See:

- [prep/txtrs/reports/narrative_plan_analysis.md](/home/donboyd5/Documents/python_projects/pension_model/prep/txtrs/reports/narrative_plan_analysis.md)
- [prep/txtrs/reports/source_sufficiency_summary.md](/home/donboyd5/Documents/python_projects/pension_model/prep/txtrs/reports/source_sufficiency_summary.md)
- [prep/txtrs/reports/selected_field_lineage.md](/home/donboyd5/Documents/python_projects/pension_model/prep/txtrs/reports/selected_field_lineage.md)

## Data/Config Issues Relevant To `txtrs-av`

For a source-first `txtrs-av` effort, the most relevant currently known issues
are:

- [#52](https://github.com/donboyd5/pension_model/issues/52): acquire and
  document the retiree mortality source and `Scale UMP 2021` implementation
- [#53](https://github.com/donboyd5/pension_model/issues/53): classify legacy
  model-mediated retiree and term-vested benefit inputs
- [#54](https://github.com/donboyd5/pension_model/issues/54): duplicate of the
  same legacy-input classification issue

Those are relevant because they affect whether a `txtrs-av` first cut can claim
to be source-direct, legacy-compatible, estimated, or runtime-only for specific
artifacts.

## Recommended First Step For `txtrs-av`

The best next step is:

- start `txtrs-av` as a controlled first-cut intake using the shared package

Operationally, that means:

- create `prep/txtrs-av/` from the shared intake templates
- anchor the source set on the latest AV first
- keep the first cut simple
- copy only the TXTRS-shaped config/data structure that is needed to stand up a
  runnable `plans/txtrs-av/`
- classify every imported field as source-direct, derived, computed,
  runtime-only, or legacy-compatible
- do not silently inherit unresolved `txtrs` compatibility artifacts as if they
  were source-direct

## Ready-To-Start Answer

`txtrs-av` is ready to start now under the repo's current state if we use the
following standard:

- controlled first cut
- AV-first
- data/config changes only
- explicit classification of compatibility artifacts
- no promise that retiree mortality or retiree-distribution sourcing is already
  solved

That is the right threshold for beginning the new plan.
