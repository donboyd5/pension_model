# scripts/

Utility scripts, organized by role. Run from the repo root.

## extract/

R and Python scripts that pull data from the R source models into an
intermediate form. Most R scripts `setwd()` into a `R_model/R_model_*/`
project first and write to `baseline_outputs/` (recreated on demand).

## build/

Python scripts that transform intermediate/extracted data into the
long-format CSVs and JSON the model actually reads from
`plans/<plan>/data/` and `plans/<plan>/baselines/`.

- `build_r_truth_tables.py` — regenerates the frozen R-model truth
  tables under `plans/<plan>/baselines/r_truth_table.csv`.
- `convert_frs_to_stage3.py` / `convert_txtrs_to_stage3.py` — full
  pipeline from extracted data into the stage-3 plan data format.
- `decrement_builder.py`, `generate_entrant_profiles.py`,
  `generate_separation_tables.py` — focused sub-steps.

## run/

Entry points for running R models directly. The Python model has its
own CLI — use `pension-model run <plan>`.

## scratch/

Gitignored working space for throwaway debug/exploration scripts.
Promote anything worth keeping into `extract/` or `build/`.
