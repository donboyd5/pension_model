# Start Refactor Plan

## Immediate Goal

Improve readability and architectural clarity while preserving exact current behavior and exact R-baseline matching.

This is not a redesign pass. It is a behavior-preserving cleanup pass.

## Rules For This Phase

- R-match remains mandatory.
- No actuarial formula changes.
- No silent "fixes" to behavior that appears questionable.
- Prefer smaller functions and clearer boundaries only when the split reflects real responsibilities.
- Keep data loading, config interpretation, and core math more clearly separated.

## First Implementation Slice

### 1. Clarify and stabilize the config boundary

- add or use typed `PlanConfig` properties where code currently reaches into `raw`
- remove mutation of frozen config objects
- keep runtime-derived artifacts explicit rather than hidden

### 2. Remove core pipeline boundary leaks

- stop reading files from inside the liability pipeline
- compute derived input facts during loading/preparation instead

### 3. Improve readability of public orchestration paths

- add targeted type hints on key public/core functions
- remove a few defensive `hasattr` / `getattr` checks where `PlanConfig` already guarantees the field

## Explicitly Deferred

- changing actuarial logic
- broad test rationalization
- raw-PDF-to-model-input ingestion pipeline
- major data-format migration such as stacking all per-class files
- funding-engine redesign
- member-status redesign

## Success Criteria For This Start Phase

- model outputs are unchanged
- R-baseline tests still pass
- `PlanConfig` is not mutated in place during loading
- the core pipeline no longer reads plan CSVs during computation
- the runtime flow is easier to follow in config loading and pipeline orchestration
