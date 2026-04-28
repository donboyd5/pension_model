# Plan-Rule Resolver Framework Implementation Plan

This document is the implementation plan for the shared plan-rule resolver
framework. It is paired with
[Alabama/Arkansas Data Collection Plan](alabama_arkansas_data_collection_plan.md),
which covers source documents and data inputs only.

The source context for this work is
[Alabama and Arkansas Pension Extension Context](alabama_arkansas_pension_extension_context.md).

## Purpose And Scope

The first implementation step for extending the model to Alabama ERS and
Arkansas APERS is a behavior-preserving rule framework. The goal is to move
current FRS and TXTRS rule resolution behind an explicit `PlanRules`
abstraction before adding new plan content.

This phase must not add Alabama ERS or Arkansas APERS plan configs. It must
not redesign data loading, segmented service, DROP accounting, or funding. It
should create a clean internal rule boundary while keeping all current public
imports and FRS/TXTRS results stable.

The framework should initially cover:

- tier assignment
- retirement status and eligibility
- FAC window selection
- COLA resolution
- benefit multiplier resolution
- early retirement reduction resolution

## Current Resolver Surfaces

The current stable public resolver surface is exported through
`src/pension_model/plan_config.py`:

- `get_tier`
- `get_tier_vectorized`
- `get_ben_mult`
- `get_reduce_factor`
- `resolve_tiers_vec`
- `resolve_tiers_vec_str`
- `resolve_cola_vec`
- `resolve_ben_mult_vec`
- `resolve_reduce_factor_vec`

The implementation is currently split across:

- `src/pension_model/config_resolvers.py`
- `src/pension_model/config_resolvers_scalar.py`
- `src/pension_model/config_resolvers_vectorized.py`
- `src/pension_model/config_resolver_common.py`

Downstream runtime callers rely on these functions from the benefit-table and
decrement-loading paths. In particular, benefit-table construction currently
uses the vectorized resolver path heavily, so the framework should keep
vectorized methods as the primary runtime contract.

## Target Abstraction

Add a new rules package under `src/pension_model/rules/`.

Recommended module layout:

- `src/pension_model/rules/__init__.py`
- `src/pension_model/rules/base.py`
- `src/pension_model/rules/table_driven.py`
- `src/pension_model/rules/factory.py`

`base.py` should define a `PlanRules` protocol or abstract base class. The
initial implementation should be a `TableDrivenPlanRules` class that reproduces
today's JSON-driven FRS/TXTRS behavior exactly.

Recommended `PlanRules` method boundary:

```python
class PlanRules(Protocol):
    def resolve_tiers(
        self,
        class_name,
        entry_year,
        age,
        yos,
        entry_age=None,
    ) -> tuple[np.ndarray, np.ndarray]:
        ...

    def resolve_tier_labels(
        self,
        class_name,
        entry_year,
        age,
        yos,
        entry_age=None,
    ) -> np.ndarray:
        ...

    def resolve_cola(
        self,
        tier_id,
        entry_year,
        yos,
    ) -> np.ndarray:
        ...

    def resolve_benefit_multiplier(
        self,
        class_name,
        tier_id,
        ret_status,
        dist_age,
        yos,
        dist_year,
    ) -> np.ndarray:
        ...

    def resolve_early_reduction(
        self,
        class_name,
        tier_id,
        ret_status,
        dist_age,
        yos,
        entry_year,
    ) -> np.ndarray:
        ...

    def resolve_fas_years(
        self,
        tier_id,
        class_name=None,
        entry_year=None,
        yos=None,
    ) -> np.ndarray:
        ...
```

The method signatures should accept the current arrays directly. Do not require
new domain objects in hot paths unless profiling shows that the overhead is
negligible.

## Implementation Sequence

1. Inventory current behavior.
   - List every public resolver and its current signature.
   - Identify scalar-only helpers and vectorized helpers.
   - Confirm current integer status constants: `NON_VESTED`, `VESTED`,
     `EARLY`, and `NORM`.
   - Confirm current tier id conventions: ids are positional indexes into
     `PlanConfig.tier_defs`.

2. Add the rules package skeleton.
   - Create `src/pension_model/rules/__init__.py`.
   - Create `src/pension_model/rules/base.py`.
   - Create `src/pension_model/rules/table_driven.py`.
   - Create `src/pension_model/rules/factory.py`.
   - Export `PlanRules`, `TableDrivenPlanRules`, and `build_plan_rules`.

3. Implement `TableDrivenPlanRules`.
   - Move or wrap the current vectorized logic from
     `config_resolvers_vectorized.py`.
   - Move or wrap the current scalar logic from
     `config_resolvers_scalar.py`.
   - Keep shared helpers either in `config_resolver_common.py` temporarily or
     move them into the rules package if the move is mechanical and low risk.
   - Preserve all NaN behavior, dtype choices, and status codes.

4. Add a rule factory.
   - Implement `build_plan_rules(config: PlanConfig) -> PlanRules`.
   - Initially always return `TableDrivenPlanRules(config)`.
   - Keep the factory simple. Do not introduce registry behavior until a
     second concrete rules implementation exists.

5. Preserve the public resolver API.
   - Keep `pension_model.plan_config` exports unchanged.
   - Keep `pension_model.config_resolvers` exports unchanged.
   - Convert public resolver functions into wrappers around
     `build_plan_rules(config)`.
   - Avoid changing call sites in the first pass unless necessary.

6. Add a low-overhead rules cache if needed.
   - If constructing `TableDrivenPlanRules` per resolver call is measurable,
     add a private cache keyed by `id(config)` or another safe config identity.
   - Do not mutate the frozen `PlanConfig` unless the design is explicitly
     reviewed.
   - Make the cache an implementation detail of the resolver wrapper or
     factory.

7. Introduce the FAC rule boundary.
   - Replace direct benefit-table lookup of `constants._tier_id_to_fas_years`
     with `rules.resolve_fas_years(...)`.
   - For current FRS and TXTRS, return exactly the same tier-based FAC years.
   - Keep output column names unchanged: `fas_period` and `fas`.

8. Add optional future context fields without activating them.
   - If a typed rule input object is introduced, reserve optional fields for
     future plans: `employer_id`, `subgroup`, `hire_date`, `actual_service`,
     `credited_service`, and `service_segments`.
   - Current FRS/TXTRS paths should not need to populate these fields.
   - Avoid forcing APERS or Alabama concepts into the current runtime tables in
     this phase.

9. Add direct rules tests.
   - Add focused tests for `TableDrivenPlanRules` using the existing FRS and
     TXTRS resolver grids.
   - Verify direct `TableDrivenPlanRules` calls match the existing public
     scalar wrappers.
   - Verify public wrappers still match their prior behavior.

10. Keep broad compatibility tests passing.
    - Run current resolver tests unchanged.
    - Run current plan config tests unchanged.
    - Run current benefit-table contract tests unchanged.
    - Run a broader suite after focused tests pass.

11. Update documentation.
    - Add a short section to `docs/architecture_map.md` describing the rules
      layer after implementation.
    - Link this plan from that section.
    - State that current FRS/TXTRS rules use `TableDrivenPlanRules`.

12. Defer plan-specific expansion.
    - Do not add Alabama-specific employer-option rules in this phase.
    - Do not add APERS segmented-service rules in this phase.
    - Do not move DROP from funding into rules in this phase.

## Compatibility Requirements

FRS and TXTRS are the compatibility baseline for this work.

The implementation must preserve:

- public imports from `pension_model.plan_config`
- public imports from `pension_model.config_resolvers`
- integer status codes
- tier id assignment order
- tier label strings, including status suffixes
- COLA proration behavior
- FAS period behavior
- benefit multiplier outputs
- early retirement reduction outputs
- NaN behavior for unresolved reduction or multiplier cases
- downstream benefit-table column names

No existing FRS or TXTRS plan config JSON should need to change.

## Test Commands

Run these focused checks first:

```powershell
python -m pytest tests/test_pension_model/test_vectorized_resolvers_frs.py -q
python -m pytest tests/test_pension_model/test_vectorized_resolvers_txtrs.py -q
python -m pytest tests/test_pension_model/test_plan_config_frs.py tests/test_pension_model/test_plan_config_txtrs.py -q
python -m pytest tests/test_pension_model/test_benefit_table_contracts.py -q
```

Then run a broader check:

```powershell
python -m pytest tests/test_pension_model -q
```

If the full suite is too slow for the implementation loop, run the focused
checks after every meaningful refactor and the full suite before considering
the phase complete.

## Acceptance Criteria

The phase is complete when:

- A `PlanRules` boundary exists and is used by the public resolver wrappers.
- `TableDrivenPlanRules` reproduces current FRS and TXTRS behavior.
- Existing resolver tests pass unchanged.
- Existing plan config tests pass unchanged.
- Benefit-table contract tests pass unchanged.
- No Alabama or APERS plan content has been added.
- No data collection or source-document work has been mixed into the rules
  implementation.
- Documentation identifies the rules package as the extension point for future
  plan behavior.

## Assumptions

- This is an architecture step, not a plan implementation step.
- FRS and TXTRS output compatibility is mandatory.
- The first rules implementation should stay close to current code to reduce
  regression risk.
- Richer service accounting, employer options, and plan-specific DROP behavior
  will be added in later phases after this boundary exists.
- It is acceptable for some helper names to remain transitional if public
  behavior and module boundaries become clearer.
