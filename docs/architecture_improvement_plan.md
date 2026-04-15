# Architecture Improvement Plan

## Goal

Move the pension model toward a design that looks like a clean, purpose-built Python system rather than a generalized port of plan-specific R models.

The target state is:

- one clear canonical config model
- one clear canonical input data model
- pure projection engines with minimal compatibility shims
- plan differences expressed in config and data, not in code branches
- modular code organized by actuarial/domain responsibilities rather than by history

## High-Priority Improvements

### 1. Replace the oversized config compatibility layer with a typed schema

Current state:

- `src/pension_model/plan_config.py` is very large and does several jobs at once: file loading, scenario merging, validation, tier resolution, plan-design lookup, compatibility adapters, and plan discovery.
- `PlanConfig` still exposes `raw` and several `SimpleNamespace` adapters, which indicates the rest of the code is still partially written against an older config shape.
- Config fields still carry legacy naming and fallback behavior such as `before_2018` vs `before_new_year`.

Why this matters:

- This is the main boundary between plan-specific data and the engine.
- If this layer is not crisp, the rest of the code cannot become crisp.

Target state:

- split config code into smaller modules: schema, loader, validator, tier resolver, plan discovery
- introduce strongly typed section objects for economic, benefit, funding, ranges, mortality, and plan design
- keep parsed JSON out of the engine except where explicitly unavoidable
- make scenario override validation happen before runtime

### 2. Define a canonical stacked input data model

Current state:

- stage-3 inputs are partly standardized, but the repo still relies heavily on per-class files such as `{class}_salary.csv`, `{class}_headcount.csv`, `{class}_termination_rates.csv`
- loaders contain fallback logic between class-specific and shared filenames
- some core logic still reaches back into files during computation

Why this matters:

- the current file layout is workable for two plans, but it will become expensive to maintain as more plans and statuses are added
- a general model should treat class, tier, status, and lookup type as data columns, not as file naming conventions

Target state:

- move toward stacked domain tables with explicit identifier columns, for example:
  - `demographics/salary.csv`
  - `demographics/headcount.csv`
  - `decrements/termination_rates.csv`
  - `decrements/retirement_rates.csv`
- require columns like `plan`, `class_name`, `tier`, `status`, `lookup_type`
- keep per-plan directories, but minimize per-class file proliferation
- make loaders responsible only for reading and validating canonical tables, not for reconstructing structure from filenames

### 3. Remove file I/O and data reconstruction from core math paths

Current state:

- the design goal says the core projection code should take inputs and return outputs with no file reading or writing
- but `compute_adjustment_ratio()` in `src/pension_model/core/pipeline.py` still reads CSVs from disk during the pipeline

Why this matters:

- this is exactly the kind of boundary leak that makes the engine feel like a historical port instead of a clean design
- it also makes testing and reuse harder

Target state:

- all file I/O stays in loaders
- all derived inputs needed by the core are computed before entering the core projection
- the pipeline receives fully prepared in-memory structures only

### 4. Break up the monolithic engine modules by domain

Current state:

- several files are now architecture bottlenecks:
  - `src/pension_model/plan_config.py`
  - `src/pension_model/core/benefit_tables.py`
  - `src/pension_model/core/_funding_core.py`
  - `src/pension_model/core/pipeline.py`
- these files mix orchestration, business rules, compatibility logic, and domain math

Why this matters:

- large files are not automatically bad, but these ones are carrying too many responsibilities
- they make it hard to see the stable abstractions of the model

Target state:

- split by responsibility, not by historical sequence
- likely module groups:
  - `config/`
  - `data/`
  - `benefits/`
  - `workforce/`
  - `funding/`
  - `validation/`
- keep public orchestration thin and push rule logic into focused modules

### 5. Rework funding into explicit strategies and state objects

Current state:

- funding already has partial strategy separation, but `_funding_core.py` still contains a very large amount of tightly coupled logic
- comments and code still explicitly reference FRS/TRS behavior and special cases such as DROP handling
- the engine is heavily column-name driven (`*_legacy`, `*_new`, DB/DC/CB combinations)

Why this matters:

- funding is one of the hardest places to generalize cleanly
- this is where future plans will most likely force awkward branching if the abstraction is not improved now

Target state:

- define explicit funding state objects for yearly balances and contribution components
- isolate strategy families:
  - AVA smoothing
  - amortization policy
  - statutory contribution schedule
  - plan-level vs class-level aggregation
- make DROP and similar features model extensions, not hidden funding-side patches

### 6. Move toward explicit member-status cohort modeling

Current state:

- the repo goals already say this is the right long-term direction
- current workforce/funding logic still approximates some statuses, especially DROP

Why this matters:

- this is the right generalization axis for public pension systems
- it will simplify future support for deferred vested, disability, survivor, and richer DROP variants

Target state:

- explicit status model such as:
  - active
  - deferred_vested
  - refund_pending
  - retiree
  - drop
  - survivor
  - disabled
- transitions expressed in tables/config, not hidden adjustments

### 7. Align documentation with the actual architecture

Current state:

- `docs/developer.md` describes packages such as `pension_config` and `pension_tools` that do not exist in the repo
- some documentation still describes the desired architecture rather than the present one

Why this matters:

- documentation drift is a reliable signal that the architecture is still in transition
- it makes future cleanup harder because the intended boundaries are not documented accurately

Target state:

- document the system as it exists now
- separately document the target architecture and migration steps
- add concise ADR-style notes when preserving R behavior or keeping temporary compatibility shims

## Recommended Sequence

### Phase 1: Stabilize boundaries

1. split `plan_config.py` into smaller modules without changing behavior
2. remove file I/O from `pipeline.py`
3. document the canonical current runtime data structures
4. update developer docs to match the real package structure

### Phase 2: Standardize data and config

1. define canonical schemas for config sections and stage-3 tables
2. add validation at load time with clear error messages
3. convert plan data toward stacked files where it reduces special handling
4. keep compatibility loaders temporarily so existing plans still run

### Phase 3: Refactor the engines

1. split benefit-table logic into smaller modules
2. split funding into strategy modules and state builders
3. make pipeline orchestration thin and declarative
4. preserve R-match tests throughout

### Phase 4: Improve model generality

1. introduce explicit member-status modeling
2. replace DROP approximations with a true status/sub-cohort implementation
3. add a third plan only through config and data to prove the architecture

## Suggested Acceptance Criteria

- adding a new plan does not require editing Python code
- config validation failures are caught before projection starts
- core compute modules do not read files or depend on raw JSON dicts
- key engine files are small enough that responsibilities are obvious
- docs describe both current architecture and target architecture truthfully
- existing FRS and TXTRS R-baseline tests still pass after each phase
