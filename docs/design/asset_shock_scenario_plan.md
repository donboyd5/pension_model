# Asset Shock Scenario Plan

## Context

Add the R asset shock scenario to the Python model, with validation that Python matches the R model results for both FRS and TXTRS. This work adds the scenario definition, incorporates a year-by-year asset return path into the Python return stream, generates R truth-table baselines, and extends the existing R-vs-Python scenario regression test matrix.

The scenario JSON uses a year-keyed mapping:

```json
{
  "asset_return_path": {
    "1": "model_return",
    "2": 0.03,
    "3": -0.24,
    "4": 0.12,
    "5": 0.12,
    "6": 0.12,
    "default": "model_return"
  }
}
```

This is the right shape for this repo because it is explicit, stable in diffs, and does not require plan-specific return CSVs.

## Current State

- `scenarios/low_return.json` can only override a flat `economic.model_return`.
- `src/pension_model/core/returns.py` currently builds a flat return stream from `constants.model_return`; its module docstring already identifies year-by-year paths as the intended follow-up.
- `src/pension_model/core/_funding_setup.py` consumes `build_return_stream(constants)` and applies the existing first-projection-year seed rule for smoothing.
- `tests/test_pension_model/test_truth_table_scenarios.py` compares Python truth tables to R baseline CSVs for `baseline`, `low_return`, and `high_discount` across FRS and TXTRS.
- R scenario runners are `scripts/run/run_r_scenario.R` for FRS and `scripts/run/run_r_scenario_txtrs.R` for TXTRS.
- Scenario R baselines live in `plans/<plan>/baselines/r_truth_table_<scenario>.csv`.

## Scenario JSON Change

Add `scenarios/asset_shock.json`:

```json
{
  "name": "asset_shock",
  "description": "Asset return shock: model return in year 1, 3% in year 2, -24% in year 3, 12% recovery in years 4-6, then model return.",
  "overrides": {
    "economic": {
      "asset_return_path": {
        "1": "model_return",
        "2": 0.03,
        "3": -0.24,
        "4": 0.12,
        "5": 0.12,
        "6": 0.12,
        "default": "model_return"
      }
    }
  }
}
```

Interpret the integer keys as projection years relative to `ranges.start_year`:

- key `"1"` applies to calendar year `start_year + 1`
- key `"2"` applies to calendar year `start_year + 2`
- values outside the explicit keys use `"default"`
- `"model_return"` means the loaded scenario's `economic.model_return`, not necessarily the baseline value

Keep the mapping under `overrides.economic` so all rate and return assumptions remain in the existing scenario override section.

## Python Incorporation Plan

The code already has a shared `build_return_stream()` helper used by DB funding and cash-balance crediting. This work extends that helper so it can resolve both the existing flat `model_return` assumption and the new year-keyed `asset_return_path`. The full R-vs-Python truth-table regression verifies the resulting model behavior.

1. Extend the config contract.

   Add an optional `asset_return_path` field to `PlanConfig` in `src/pension_model/config_schema.py`, populated from `raw["economic"].get("asset_return_path")` in `src/pension_model/config_loading.py`.

2. Update `build_return_stream`.

   Modify `src/pension_model/core/returns.py` so:

   - no `asset_return_path` keeps current flat behavior
   - explicit year keys map to `constants.start_year + projection_year`
   - `"model_return"` resolves to `constants.model_return`
   - numeric values are used directly
   - every year in `min_entry_year..max_year` receives a value

3. Use one resolved stream for both consumers.

   Keep `src/pension_model/core/returns.py::build_return_stream()` as the single place that translates scenario/config return assumptions into an annual `pd.Series`. Then make both current consumers use the same resolved stream:

   - cash-balance crediting, through the `_return_scenario` attached during input loading
   - DB funding, through the funding context's `ret_scen`

   Both paths should call the same helper and therefore get identical values.

4. Preserve the existing funding seed rule.

   Leave `_build_return_stream_for_funding()` in `src/pension_model/core/_funding_setup.py` responsible for the first-projection-year smoothing pin. For this asset shock path, year 1 is already `"model_return"`, so the rule should not change the scenario's intended shock timing.

## Bounded Asset-Return Cleanup

As part of this plan, finish the asset-return cleanup that directly supports `asset_shock`:

- `build_return_stream()` remains the only translation layer from config/scenario return assumptions to year-indexed returns.
- Flat `economic.model_return` scenarios keep their current behavior.
- Year-keyed `economic.asset_return_path` scenarios use the same stream consumed by DB assets and cash-balance actual ICR.
- Use the full R-vs-Python truth-table regression to verify `asset_shock` behavior.

## R Baseline Plan

1. Add `asset_shock` branches to both R scenario runners:

   - `scripts/run/run_r_scenario.R`
   - `scripts/run/run_r_scenario_txtrs.R`

2. Drive the R model through its existing return-scenario mechanism.

   The FRS and TXTRS R funding models already use `return_scenarios` plus a selected `return_scen`. The R runner should create or select the same path as the JSON:

   - year 1: model return
   - year 2: `0.03`
   - year 3: `-0.24`
   - years 4-6: `0.12`
   - later years: model return

3. Generate and commit these R truth tables in the same way as `low_return` and `high_discount`:

   - `plans/frs/baselines/r_truth_table_asset_shock.csv`
   - `plans/txtrs/baselines/r_truth_table_asset_shock.csv`

   FRS:

   ```powershell
   Push-Location R_model\R_model_frs
   Rscript ..\..\scripts\run\run_r_scenario.R asset_shock
   Pop-Location
   ```

   TXTRS:

   ```powershell
   Push-Location R_model\R_model_txtrs
   Rscript ..\..\scripts\run\run_r_scenario_txtrs.R asset_shock
   Pop-Location
   ```

## Regression Test Plan

Update `tests/test_pension_model/test_truth_table_scenarios.py`:

- include `("frs", "asset_shock")`
- include `("txtrs", "asset_shock")`
- update the module coverage comment and parametrized `ids`

The existing test function can remain unchanged because `_scenario_path()` already resolves `scenarios/{scenario}.json` and `_r_baseline_path()` already resolves `r_truth_table_{scenario}.csv`.

Also update `Makefile`:

```make
SCENARIOS ?= baseline low_return high_discount asset_shock
```

That keeps `make run-all` aligned with the tested scenario matrix.

## Verification Commands

After implementation and R baseline generation:

```powershell
python -m pytest tests/test_pension_model/test_truth_table_scenarios.py -v
python -m pytest tests/test_pension_model/test_plan_config_frs.py tests/test_pension_model/test_plan_config_txtrs.py -v
```

## Acceptance Criteria

- `scenarios/asset_shock.json` uses the year-keyed mapping.
- Python can load and run `asset_shock` for FRS and TXTRS without plan-specific code.
- The return stream applies the shock to the intended projection years and falls back to `model_return` afterward.
- R truth tables exist for FRS and TXTRS asset shock.
- `test_truth_table_matches_r_baseline` includes and passes both asset shock cells.
- Existing `baseline`, `low_return`, and `high_discount` R-match tests still pass.
