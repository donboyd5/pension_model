# Testing Strategy

This document proposes how the pension-model test suite should evolve from its current "match R while refactoring" shape into a cleaner long-run validation system.

The central idea is:

- some tests are permanent because they protect the model's mathematical and architectural contracts
- some tests are transitional because they protect the current R-reproduction phase
- every plan should eventually have a reviewed baseline truth, even when no external R model exists
- important policy scenarios may also deserve reviewed "truth" baselines

The goal is not fewer tests for its own sake. The goal is a suite whose purpose is explicit, whose default runtime is reasonable, and whose long-run maintenance burden matches the model's actual needs.

## Why This Matters

Today the suite mixes several different jobs:

- local unit checks
- internal consistency checks
- exact or near-exact reproduction of FRS/TXTRS reference results
- refactor-era anti-drift snapshots
- data integrity checks
- development-only checks tied to historical Excel or R extraction workflows

Those are all legitimate, but they should not all be treated the same way. If they are, we end up with:

- slow default runs
- unclear expectations for `pension-model run <plan>`
- tests that linger after their main job is done
- difficulty deciding what should block a change versus what should only inform it

## Two Kinds of Truth

The suite should treat "truth" more broadly than "R truth."

### External truth

This is truth anchored outside the Python model:

- R reference models for FRS and TXTRS
- actuarial valuation report targets
- extracted historical intermediate outputs
- source Excel workbooks used during initial migration or reconciliation

External truth is especially valuable in the early stages of a port or generalization effort.

### Reviewed internal truth

This is truth anchored in the Python model after careful review:

- a reviewed baseline run for a plan with no external R model
- a reviewed set of funding outputs, liability outputs, or key intermediate tables
- a reviewed truth table or selected subset of truth-table columns
- a reviewed policy-scenario run used as an anti-drift reference

Reviewed internal truth matters because eventually the Python model becomes the primary maintained system. At that point, the question is not only "does this still match R?" but also "did this drift from our reviewed canonical result?"

## Test Taxonomy

The suite should be organized around purpose, not around historical file names.

### 1. Unit tests

Scope:

- single functions
- small resolvers
- narrow builders
- formatting or schema helpers

Purpose:

- isolate bugs quickly
- make refactors safer
- keep failures local and readable

These are permanent.

### 2. Invariant tests

Scope:

- actuarial identities
- accounting identities
- shape and conservation rules that should hold for any valid plan
- structural behaviors such as rundown logic or funded-ratio identities

Purpose:

- verify the model's contracts independent of any one reference plan

These are permanent and should become the long-run backbone of the suite.

### 3. Reviewed-baseline regression tests

Scope:

- baseline outputs for a specific plan compared with a reviewed canonical result

Possible truth sources:

- external R truth
- reviewed Python truth
- reviewed AV-target comparisons

Purpose:

- prevent accidental drift in key outputs

These are permanent in concept, though the source of truth may change over time.

### 4. Reviewed-policy regression tests

Scope:

- selected scenario outputs compared with reviewed canonical scenario results

Examples:

- low-return scenario
- no-COLA scenario
- closed-plan / no-new-entrants scenario
- a scenario used in published policy work

Purpose:

- prevent drift in policy-relevant behavior, not just in baseline plumbing

These are likely permanent for a small curated set of scenarios.

### 5. Snapshot / refactor-guard tests

Scope:

- exact snapshots of current outputs or intermediate structures created to protect a refactor phase

Purpose:

- catch even tiny unintended drift during architectural cleanup

These are useful, but they are not automatically permanent. Some should be retired once the underlying refactor phase is complete or replaced by cleaner reviewed-baseline tests.

### 6. Data / fixture integrity tests

Scope:

- shared decrement files
- fixture consistency
- canonical baseline and snapshot files

Purpose:

- catch accidental corruption or divergence of committed inputs

These are permanent.

### 7. Transitional external-truth tests

Scope:

- tests whose main job is to verify the Python model against an external legacy implementation or legacy extraction workflow during an early development phase

Purpose:

- protect the "match R first" phase

These are explicitly transitional. They may be reduced, re-scoped, or retired once the model has a sufficiently strong reviewed-baseline and invariant suite.

## Retention Policy

Each test or test file should be classified as one of:

- `permanent`
- `transitional`
- `refactor_phase`

### Permanent

These should remain even after R is no longer the primary development anchor:

- unit tests
- invariant tests
- data integrity tests
- curated reviewed-baseline regressions
- curated reviewed-policy regressions

### Transitional

These are justified mainly because the repo is still in the "exact reproduction of current R results" phase.

Examples:

- broad FRS/TXTRS extracted-R intermediate comparisons
- tests tied to temporary dual-path validation against legacy build workflows

They should not stay forever by inertia. When the project decides a plan is no longer "R-load-bearing," these tests should be reviewed intentionally.

### Refactor-phase

These exist to protect a bounded cleanup or unification effort.

Examples:

- exact funding snapshots created during funding-model unification

They should be reviewed after the refactor stabilizes. Some will graduate into permanent reviewed-baseline tests; others should be removed.

## Run Profiles

The repo should eventually expose a few explicit test profiles instead of treating every run as "all tests."

### `fast`

Purpose:

- developer inner loop

Contents:

- unit tests
- small invariants
- data integrity checks

Should avoid:

- full-plan end-to-end regressions
- large snapshots
- long-run rundown tests
- Excel-dependent historical checks

### `standard`

Purpose:

- normal local validation before merge

Contents:

- unit tests
- invariants
- data integrity tests
- reviewed-baseline regressions for the plan being worked on
- a small number of representative cross-plan checks

This should be the likely target for `pension-model run <plan>` after the CLI is rationalized.

### `full`

Purpose:

- CI, release, or major refactor gate

Contents:

- the entire suite, including:
- cross-plan regressions
- snapshots
- rundown tests
- transitional external-truth checks

### `plan:<name>`

Purpose:

- run shared core tests plus plan-specific regressions for a named plan

Examples:

- `plan:frs`
- `plan:txtrs`

This is important because the current CLI behavior is broader than a user likely expects.

As of April 16, 2026, `pension-model run frs` does **not** run an FRS-only subset. It runs:

```text
python -m pytest tests/test_pension_model/ -v --tb=short
```

That executes the full suite, including TXTRS and cross-plan tests. This is acceptable as a temporary default, but it is not the desired long-run behavior.

## Recommended Truth Model by Plan

Every plan should eventually have some form of reviewed baseline comparison.

### FRS and TXTRS now

Use:

- external R truth
- AV targets
- selected reviewed intermediate outputs

These remain the strongest current anchors.

### New plans without external truth

Use:

- reviewed baseline outputs
- reviewed intermediate outputs where they matter
- invariant checks
- AV-target comparisons

The absence of an R model does not mean the absence of truth. It means the truth source is a reviewed canonical Python result rather than an external legacy model.

### Policy scenarios

For a small set of important scenarios, the repo should keep reviewed policy truths.

Candidate scenario classes:

- low return
- high discount
- no COLA
- closed plan / no new entrants
- plan-specific scenarios used in published analysis

Only a curated set should be promoted to reviewed policy truth. Otherwise scenario testing can expand without discipline.

## First-Pass Classification of the Current Suite

This is a proposed starting point, not a final classification.

| File | Primary Role | Retention |
|------|--------------|-----------|
| `test_vectorized_resolvers.py` | unit | permanent |
| `test_plan_config.py` | unit / config contract | permanent |
| `test_data_integrity.py` | data integrity | permanent |
| `test_consistency.py` | invariants | permanent |
| `test_truth_table.py` | invariants / output contract | permanent |
| `test_rundown.py` | invariant / behavioral scenario | permanent, but `slow` |
| `test_multi_class_gainloss.py` | architectural regression for generalized funding behavior | likely permanent |
| `test_funding_baseline.py` | reviewed-baseline regression using external R truth | permanent concept, transitional truth source |
| `test_stage3_loader.py` | transitional external-truth / migration-path validation | transitional |
| `test_benefit_tables.py` | mixed: some unit, some extracted-R regression | split later; mixed today |
| `test_calibration.py` | mixed: reviewed-baseline regression plus calibration sanity | mixed today |
| `test_funding_snapshots.py` | refactor-phase snapshot guard | refactor_phase, review later |

## What Should Likely Change First

This document is intentionally policy-first. Before rewriting the suite heavily, the repo should make a few small structural changes.

### 1. Add clearer pytest markers

Current markers are too coarse:

- `unit`
- `integration`
- `slow`

The suite likely needs markers closer to:

- `unit`
- `invariant`
- `regression`
- `policy`
- `snapshot`
- `data`
- `transitional`
- `slow`
- possibly `plan_frs` / `plan_txtrs`

### 2. Stop treating `pension-model run <plan>` as "run everything"

Long-run desired behavior:

- `pension-model run frs` should run shared core tests plus FRS-relevant regressions
- `pension-model run txtrs` should run shared core tests plus TXTRS-relevant regressions
- the full cross-plan suite should remain available explicitly

### 3. Split mixed-purpose files

Some files currently mix unit, regression, and transitional checks. Those should eventually be separated so retention and runtime decisions are easier.

Likely candidates:

- `test_benefit_tables.py`
- `test_calibration.py`

### 4. Replace broad historical dependence with curated reviewed baselines

Over time, some broad extracted-R or Excel-path checks should give way to:

- a smaller reviewed baseline comparison set
- stronger invariants
- targeted regression tests for historically broken behaviors

That reduces maintenance burden without weakening protection.

## Practical Next Step After This Doc

The next implementation pass should be small and mechanical:

1. add or tighten pytest markers
2. classify each current file or test class by marker
3. update the developer docs to reference this taxonomy
4. narrow the CLI's default post-run test command so it is not always the full suite

That would improve test clarity immediately without requiring a wholesale rewrite.
