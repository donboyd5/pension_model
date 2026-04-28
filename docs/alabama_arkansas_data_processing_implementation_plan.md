# Alabama ERS And Arkansas APERS Data Processing Implementation Plan

Status: created after first implementation slice
Date: 2026-04-28

The first implementation slice has archived the primary public source PDFs and
added minimal aggregate funding, calibration, and plan config files. This
document tracks the remaining data-collection and processing work needed before
either plan should be treated as model-ready.

## Current Baseline

Implemented:

- `plans/al_ers/source_docs/`
- `plans/ar_apers/source_docs/`
- `plans/al_ers/config/plan_config.json`
- `plans/ar_apers/config/plan_config.json`
- `plans/al_ers/config/calibration.json`
- `plans/ar_apers/config/calibration.json`
- `plans/al_ers/data/funding/init_funding.csv`
- `plans/ar_apers/data/funding/init_funding.csv`
- `plans/al_ers/data/funding/return_scenarios.csv`
- `plans/ar_apers/data/funding/return_scenarios.csv`

Important limitation: the current configs are aggregate public-report baselines.
They are intended to load and preserve funding/calibration targets, not to run a
credible full liability projection yet.

## Phase 2: Digitize Public Demographics

Deliverables:

- `plans/al_ers/data/demographics/{class}_headcount.csv`
- `plans/al_ers/data/demographics/{class}_salary.csv`
- `plans/al_ers/data/demographics/retiree_distribution.csv`
- `plans/ar_apers/data/demographics/all_headcount.csv`
- `plans/ar_apers/data/demographics/all_salary.csv`
- `plans/ar_apers/data/demographics/retiree_distribution.csv`

Tasks:

1. APERS: digitize the active member age-service/payroll grids from the June
   30, 2025 valuation.
2. APERS: digitize inactive deferred annuity counts and annual annuities by
   age group.
3. Alabama ERS: determine whether the valuation membership schedules provide
   enough age-service detail for public-table extraction.
4. Alabama ERS: if only class/tier totals are public, create documented
   synthetic age-service allocations and tag them as synthetic.
5. Build retiree distributions from public schedules if available; otherwise
   build aggregate distributions calibrated to retiree count and annual
   benefit totals.

Acceptance:

- Active headcount and payroll totals reconcile to the public valuation totals.
- Retiree count and annual benefit totals reconcile to public report targets.
- Any synthetic distribution has a source note and a reproducible
  transformation note.

## Phase 3: Convert Salary Growth And Decrements

Deliverables:

- `plans/al_ers/data/demographics/{class}_salary_growth.csv` or shared
  `plans/al_ers/data/demographics/salary_growth.csv`
- `plans/ar_apers/data/demographics/salary_growth.csv`
- `plans/al_ers/data/decrements/{class}_termination_rates.csv`
- `plans/al_ers/data/decrements/{class}_retirement_rates.csv`
- `plans/ar_apers/data/decrements/termination_rates.csv`
- `plans/ar_apers/data/decrements/retirement_rates.csv`

Tasks:

1. Digitize Alabama ERS Schedule D salary increase assumptions.
2. Digitize Alabama ERS withdrawal and retirement assumptions by class/tier.
3. Digitize APERS pay increase assumptions by age.
4. Digitize APERS withdrawal, disability, retirement, and DROP entry
   assumptions from the valuation.
5. Decide how to represent disability rates if the current projection path
   cannot consume them directly.
6. Add table-level QA checks for representative cells from each source table.

Acceptance:

- Decrement files are rectangular and pass CSV schema checks.
- Representative source-table values round-trip into CSV exactly or within
  documented rounding tolerance.
- Any simplification, such as APERS actual-service versus credited-service
  collapse, is explicit in extraction notes.

## Phase 4: Build Mortality Inputs

Deliverables:

- `plans/al_ers/data/mortality/base_rates.csv`
- `plans/al_ers/data/mortality/improvement_scale.csv`
- `plans/ar_apers/data/mortality/base_rates.csv`
- `plans/ar_apers/data/mortality/improvement_scale.csv`

Tasks:

1. Source the needed SOA Pub-2010 base table data.
2. Source MP-2020 and MP-2021 improvement scales.
3. Apply Alabama ERS table multipliers, age adjustments, public safety/general
   distinctions, and the valuation's MP-2020 treatment.
4. Apply APERS PubG/PubNS table percentages and MP-2021 generational
   improvement.
5. Spot-check adjusted rates at several ages, sexes, and retiree statuses.

Acceptance:

- Mortality CSVs match the repo's existing stage-3 format.
- A reviewer can trace every adjusted table back to source table, multiplier,
  age setback, and improvement scale.

## Phase 5: Improve Plan Provisions

Deliverables:

- Updated `plans/al_ers/config/plan_config.json`
- Updated `plans/ar_apers/config/plan_config.json`
- Provision extraction notes in each plan's `source_notes/`

Tasks:

1. Extract Alabama State Police Tier 1 and Tier 2 handbook provisions.
2. Extract Alabama local 25-year retirement rules and identify the employer
   data needed to apply them.
3. Extract Alabama Act 2022-348 employer election mechanics.
4. Implement APERS service-segment multipliers if service segment data becomes
   available.
5. Implement APERS pre/post July 1, 2022 FAC and COLA cohorts using hire-date
   distributions when available.
6. Decide whether DROP remains an aggregate funding assumption or gets explicit
   participant-state modeling.

Acceptance:

- Config provisions reflect extracted rules, not placeholders.
- Known rule gaps remain in `data_gaps.md`.
- Any model limitation is visible in config notes.

## Phase 6: Request Non-Public Must-Have Data

Deliverables:

- `plans/al_ers/source_notes/data_request.md`
- `plans/ar_apers/source_notes/data_request.md`

Tasks:

1. Draft RSA request for anonymized valuation census, retiree census, deferred
   vested data, local employer rates, Act 2022-348 elections, and 25-year
   retirement flags.
2. Draft APERS request for anonymized valuation census, actual service,
   credited service, contribution design, hire date, elected-official status,
   service segment history, and DROP account data.
3. Request machine-readable assumption workbooks or experience-study tables
   from both systems.
4. Track request date, recipient, response, restrictions, and follow-up needs.

Acceptance:

- Requests are specific enough for plan staff to answer without a discovery
  meeting.
- Any denied or unavailable data is copied into `data_gaps.md` with the date
  and reason.

## Phase 7: Validate End To End

Deliverables:

- Plan-specific config and data loading tests.
- Reconciliation checks against public calibration targets.
- Updated extraction notes for any deviations.

Tasks:

1. Add tests that load `al_ers` and `ar_apers` configs.
2. Add tests that funding input totals reconcile to `calibration.json` and
   extraction-note targets.
3. Add data-file existence checks once demographics, decrements, and mortality
   are implemented.
4. Run the full model only after demographics, decrements, and mortality are
   complete enough to avoid false precision.

Acceptance:

- Aggregate funding/calibration files load.
- Public valuation totals reconcile.
- Remaining projection differences are documented as data limitations or
  implementation work.

