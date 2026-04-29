# New-Plan Readiness Status

## Purpose

This note applies the shared readiness checklist to the repo as it stands after
the FRS and TXTRS pilot work completed so far.

It answers a practical question:

- are we ready to start a genuinely new plan without first solving every
  remaining pilot mystery?

## Current Assessment

Short answer:

- almost, but not fully

The prep package is now strong enough to support a disciplined new-plan intake,
but a few shared operational pieces still need to be tightened before the repo
should be treated as fully ready.

## Status By Readiness Area

### 1. Runtime input contract

- Status: `mostly ready`
- Evidence:
  - [docs/runtime_input_contract.md](/home/donboyd5/Documents/python_projects/pension_model/docs/runtime_input_contract.md)
- Notes:
  - the runtime target is documented well enough to orient prep
  - it may still need refinement later, but it is usable as a first target for
    a new plan

### 2. AV-first source hierarchy

- Status: `ready`
- Evidence:
  - [docs/input_prep_workplan.md](/home/donboyd5/Documents/python_projects/pension_model/docs/input_prep_workplan.md)
  - [prep/common/methods/method_registry.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/methods/method_registry.md)
  - [prep/common/reports/cross_plan_lessons.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/cross_plan_lessons.md)
- Notes:
  - the rule is now explicit:
    - the AV is the source document
    - AV-referenced external tables are part of the authoritative source set
    - ACFR and similar documents are estimation or reconciliation support unless
      a plan-specific review justifies something stronger

### 3. Shared intake templates

- Status: `ready`
- Evidence:
  - [docs/narrative_plan_analysis_template.md](/home/donboyd5/Documents/python_projects/pension_model/docs/narrative_plan_analysis_template.md)
  - [prep/common/reports/source_sufficiency_summary_template.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/source_sufficiency_summary_template.md)
  - [prep/common/reports/artifact_coverage_matrix_template.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/artifact_coverage_matrix_template.md)
  - [prep/common/reports/page_crosswalk_template.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/page_crosswalk_template.md)
  - [prep/common/reports/first_year_cashflow_review_template.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/first_year_cashflow_review_template.md)
  - [prep/common/reports/mortality_basis_review_template.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/mortality_basis_review_template.md)
  - [prep/common/reports/new_plan_readiness_checklist.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/new_plan_readiness_checklist.md)
- Notes:
  - the minimum first-pass package for a new plan is now defined with shared
    templates instead of only pilot-specific examples

### 4. Provenance and source-role scaffolding

- Status: `mostly ready`
- Evidence:
  - [prep/common/schemas/source_registry_schema.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/schemas/source_registry_schema.md)
  - [prep/common/schemas/artifact_provenance_schema.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/schemas/artifact_provenance_schema.md)
  - [prep/common/source_registry.csv](/home/donboyd5/Documents/python_projects/pension_model/prep/common/source_registry.csv)
  - [prep/frs/source_registry.csv](/home/donboyd5/Documents/python_projects/pension_model/prep/frs/source_registry.csv)
  - [prep/txtrs/source_registry.csv](/home/donboyd5/Documents/python_projects/pension_model/prep/txtrs/source_registry.csv)
- Notes:
  - the source registry now has an explicit `source_role` field
  - that is enough to support AV-first intake on a new plan
  - further refinement is still likely once a real new-plan source set is in
    hand

### 5. Shared validation and checks

- Status: `ready`
- Evidence:
  - [prep/common/checks/consistency_check_catalog.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/checks/consistency_check_catalog.md)
  - [prep/common/checks/check_manifest_template.csv](/home/donboyd5/Documents/python_projects/pension_model/prep/common/checks/check_manifest_template.csv)
- Notes:
  - the repo now has an operational check catalog for source, cross-table,
    canonical-artifact, runtime-equivalence, and external-reference checks

### 6. Shared methods versus legacy-only methods

- Status: `mostly ready`
- Evidence:
  - [prep/common/methods/method_registry.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/methods/method_registry.md)
- Notes:
  - the main reusable transforms are separated from legacy-only reconstruction
    paths
  - the important boundary is now explicit:
    - FRS first-year disbursement proxy is a legacy path, not a default
      new-plan rule

### 7. Shared external reference governance

- Status: `partial`
- Evidence:
  - [prep/common/source_registry.csv](/home/donboyd5/Documents/python_projects/pension_model/prep/common/source_registry.csv)
  - [prep/common/reports/soa_reference_inventory.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/soa_reference_inventory.md)
- Notes:
  - the common source area exists and official SOA files are present
  - the governance pattern is mostly there
  - the remaining weakness is not structure; it is plan-specific external-source
    completion for cases like TX TRS retiree mortality

### 8. Need to solve all pilot mysteries first?

- Status: `no`
- Notes:
  - the repo does not need to solve every remaining FRS or TXTRS question before
    starting a new plan
  - it does need those unresolved items to remain clearly labeled as:
    - legacy-only
    - partially reconstructed
    - external-source gap
  - that condition is now mostly satisfied

## What Still Needs To Happen Before Calling The Repo Fully Ready

- apply the new intake package cleanly once from start to finish on a single
  test plan workflow, even if that plan is still FRS or TXTRS
- keep external-source handling explicit where the AV names outside tables or
  scales
- preserve the discipline that new plans start simple and AV-faithful instead
  of inheriting legacy pilot shortcuts

## Practical Conclusion

The repo is ready enough to begin a new plan cautiously if needed.

But the better standard is:

- ready for a controlled first cut
- not yet mature enough to assume every downstream wrinkle has a polished shared
  implementation

That means the right next use of the prep system would be:

- start a new plan with the defined intake package
- keep the first cut simple
- treat the first real new-plan onboarding as another design-learning pass
