# New-Plan Readiness Checklist

## Purpose

This checklist defines what should be in place before starting prep for a
genuinely new pension plan.

The goal is not to solve every open question from FRS and TXTRS first. The
goal is to make sure a new plan starts from a controlled, reusable, AV-faithful
workflow instead of from ad hoc exploration.

## Readiness Standard

A new plan is `ready to start` when the repo can support:

- an AV-first intake
- a documented source inventory
- a documented gap review
- a documented path from sources to canonical runtime inputs
- explicit handling of what is source-direct, derived, estimated, computed, or
  still missing

## Required Shared Foundations

Before starting a new plan, confirm that the following shared items exist and
are usable:

- [docs/runtime_input_contract.md](/home/donboyd5/Documents/python_projects/pension_model/docs/runtime_input_contract.md)
- [docs/narrative_plan_analysis_template.md](/home/donboyd5/Documents/python_projects/pension_model/docs/narrative_plan_analysis_template.md)
- [prep/common/schemas/source_registry_schema.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/schemas/source_registry_schema.md)
- [prep/common/schemas/artifact_provenance_schema.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/schemas/artifact_provenance_schema.md)
- [prep/common/checks/consistency_check_catalog.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/checks/consistency_check_catalog.md)
- [prep/common/reports/first_year_cashflow_review_template.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/first_year_cashflow_review_template.md)
- [prep/common/reports/mortality_basis_review_template.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/reports/mortality_basis_review_template.md)
- [prep/common/methods/method_registry.md](/home/donboyd5/Documents/python_projects/pension_model/prep/common/methods/method_registry.md)

If any of these are missing or too vague to use operationally, tighten them
before starting the new plan.

## Source Hierarchy Check

Before intake, confirm that the source hierarchy for the new plan will be:

1. actuarial valuation
2. external tables or standards explicitly named by the actuarial valuation
3. auxiliary documents used only for estimation support, reconciliation, or
   clue-mining unless a plan-specific review justifies something stronger

Operational implications:

- the AV is the source document
- the ACFR is not a co-equal source document for new-plan prep
- if prep departs from AV treatment, the departure must be labeled and
  justified

## Minimum New-Plan Intake Package

The first cut for a new plan should produce all of the following:

- narrative plan analysis
- source registry
- page crosswalk for major documents
- source sufficiency and gap report
- artifact coverage matrix
- plan-level check manifest
- first-year cash-flow review
- mortality-basis review

This first cut does not need to solve every detail. It does need to make the
state of the evidence explicit.

## Approved Versus Legacy-Only Methods

Before using a shared method on a new plan, classify it:

- `approved source-faithful transform`
- `documented estimation method`
- `legacy-only reconstruction`

Rules:

- source-faithful transforms are safe candidates for reuse
- documented estimation methods may be reused when the missing-data pattern
  matches and the method assumptions fit
- legacy-only reconstruction methods are not default methods for new plans

Examples from the pilots:

- `active-grid-band-to-point-v1`: reusable
- `entrant-profile-boundary-merge-v1`: reusable
- `first-year-disbursement-proxy-v1`: legacy path, not a default new-plan rule

## Runtime-Contract Readiness

Before starting a new plan, confirm that the runtime target is clear enough to
build toward:

- required files are known
- required columns are known
- canonical units are known
- source-derived versus computed versus runtime-only items are distinguished

If the runtime target is too ambiguous, fix that first. Otherwise new-plan prep
will drift into hidden assumptions.

## Scope Strategy Check

Before intake, agree that the new plan will be incorporated in multiple cuts:

- first cut:
  - represent the main plan structure
  - stay close to AV treatment
  - produce a usable canonical input set
- later cuts:
  - add secondary detail
  - reduce reliance on broad proxies or heavy calibration where justified

This should be documented in the narrative and gap report so simplifications are
understood as current scope choices rather than forgotten omissions.

## What Does Not Need To Be Solved First

The following do not need to be fully solved before starting a new plan:

- every remaining FRS legacy mystery
- every remaining TXTRS external-source gap
- every possible future runtime-contract refinement

But they do need to be classified well enough that they are not accidentally
treated as default practice.

## Ready-To-Start Decision

A new plan is ready to start when all of the following are true:

- the shared foundations are present
- the AV-first source hierarchy is explicit
- the minimum intake package is defined
- reusable methods are distinguishable from legacy-only methods
- the runtime target is clear enough to build toward
- the team accepts a multiple-cut onboarding strategy

If any of those conditions fail, tighten the shared prep package first.
