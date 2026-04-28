# Alabama ERS And Arkansas APERS Data Collection Plan

This document is the data-source and input-preparation plan for Alabama ERS
and Arkansas APERS. It is paired with
[Plan-Rule Resolver Framework Implementation Plan](plan_rule_resolver_framework_plan.md),
which covers Python resolver architecture only.

The source context for this work is
[Alabama and Arkansas Pension Extension Context](alabama_arkansas_pension_extension_context.md).

Before extraction, recheck the official plan websites for newer documents. The
links below are starting points and should be treated as source-control notes,
not permanent assumptions about the latest available valuation or handbook.

## Existing Repo Data Layout To Populate

Each new plan should eventually have a directory under `plans/{plan}/` matching
the current stage-3 layout.

Recommended plan ids:

- `al_ers`
- `ar_apers`

Required config files:

- `plans/{plan}/config/plan_config.json`
- `plans/{plan}/config/calibration.json`

Required demographic files:

- `plans/{plan}/data/demographics/{class}_headcount.csv`
- `plans/{plan}/data/demographics/{class}_salary.csv`
- `plans/{plan}/data/demographics/{class}_salary_growth.csv`
- or shared `plans/{plan}/data/demographics/salary_growth.csv`
- `plans/{plan}/data/demographics/retiree_distribution.csv`
- optional `plans/{plan}/data/demographics/entrant_profile.csv`

Required decrement files:

- `plans/{plan}/data/decrements/{class}_termination_rates.csv`
- `plans/{plan}/data/decrements/{class}_retirement_rates.csv`
- or shared `plans/{plan}/data/decrements/termination_rates.csv`
- or shared `plans/{plan}/data/decrements/retirement_rates.csv`
- early retirement reduction tables where the plan uses table-based reductions
- DROP entry tables if DROP is modeled explicitly in a later phase

Required mortality files:

- `plans/{plan}/data/mortality/base_rates.csv`
- `plans/{plan}/data/mortality/improvement_scale.csv`

Required funding files:

- `plans/{plan}/data/funding/init_funding.csv`
- `plans/{plan}/data/funding/return_scenarios.csv`
- optional `plans/{plan}/data/funding/amort_layers.csv`

The current model can ingest aggregate public-report data, but the Alabama and
APERS implementations will be more credible if age-service-salary census
summaries or member-level anonymized census extracts can be obtained.

## Alabama ERS Documents To Collect

Collect the latest official versions of these materials before building
`plans/al_ers`.

1. ERS member handbook.
   - Purpose: plan provisions, Tier 1/Tier 2 rules, vesting, member
     contributions, benefit formula, FAC, compensation caps, retirement
     eligibility, local employer treatment, and legacy DROP.
   - Official source page: https://www.rsa-al.gov/ers/publications/
   - Current handbook URL identified during planning:
     https://www.rsa-al.gov/uploads/files/ERS_Member_Handbook_2023.pdf

2. ERS actuarial valuation reports.
   - Purpose: valuation assets, liabilities, normal cost, contribution rates,
     member counts, payroll, assumptions, methods, amortization bases, and
     plan provisions interpreted for valuation.
   - Official source page:
     https://www.rsa-al.gov/employers/financial-reports/
   - Current FY24 valuation URL identified during planning:
     https://www.rsa-al.gov/uploads/files/ERS-Val-2024-9-30_1.pdf

3. RSA Annual Comprehensive Financial Report.
   - Purpose: financial statements, investment return, benefit payments,
     refunds, contribution totals, actuarial schedules, and historical trend
     data.
   - Official source page:
     https://www.rsa-al.gov/about-rsa/publications/annual-comprehensive-financial-report/

4. Act 2022-348 employer election material.
   - Purpose: local employer option data for providing Tier 1 benefits to
     Tier 2 members, and the implementation details needed for employer-level
     plan options.
   - Official source page:
     https://www.rsa-al.gov/employers/ers/act-2022-348/

5. Local employer rate reports or schedules.
   - Purpose: employer-specific local rates, local election effects, local
     25-year retirement options, and differences between state, state police,
     and local employers.
   - Likely source: RSA employer financial reports, local employer notices,
     or direct request to RSA.

6. Experience study or assumption report.
   - Purpose: termination, retirement, disability, salary scale, payroll
     growth, mortality, and other demographic assumptions.
   - Likely source: RSA board materials, valuation appendices, or direct
     request to RSA if not posted as a standalone document.

7. Census or tabulated valuation data.
   - Purpose: active headcount and salary by age, service, tier, class,
     subgroup, and employer type.
   - Likely source: not fully public; request from RSA or reconstruct from
     valuation report schedules if only aggregate modeling is possible.

## Arkansas APERS Documents To Collect

Collect the latest official versions of these materials before building
`plans/ar_apers`.

1. APERS member handbook.
   - Purpose: actual service, credited service, FAC, COLA, multipliers,
     contributory and non-contributory service, elected official enhanced
     service, retirement eligibility, early reductions, PAW, refund,
     restoration, and DROP.
   - Current handbook URL identified during planning:
     https://www.apers.org/wp-content/uploads/APERS-Handbook_Updated_05-01-2025.pdf

2. APERS actuarial valuation reports.
   - Purpose: employer contribution rate, assets, liabilities, normal cost,
     assumptions, methods, membership data, gain/loss, funding policy, and
     contribution schedules.
   - Current June 30, 2025 valuation URL identified during planning:
     https://apers.org/wp-content/uploads/APERS-June-30-2025-Pension-Valuation-Report.pdf

3. APERS Annual Comprehensive Financial Report.
   - Purpose: financial statements, assets, benefit payments, contribution
     totals, membership statistics, investment returns, actuarial schedules,
     and DROP accounting disclosures.
   - Current FY2024 ACFR URL identified during planning:
     https://apers.org/wp-content/uploads/APERS-ACFR-24-web.pdf

4. APERS employer reporting specifications.
   - Purpose: work-report data fields, compensation definitions, hours-to-
     service conversion, member and employer contributions, elected official
     enhanced-credit reporting, and import samples.
   - Official source page:
     https://apers.org/employers/employer-reporting/

5. APERS employer contribution rate publications.
   - Purpose: employer group rates, effective dates, member contribution rate
     ramp, and additional elected official contribution rates.
   - Official source page:
     https://apers.org/employers/employer-reporting/

6. APERS board packets or funding policy documents.
   - Purpose: contribution-rate decisions, DROP interest or crediting policy,
     amortization policy, assumption changes, and plan-policy changes not fully
     captured in the handbook.
   - Likely source: APERS board materials or direct request to APERS.

7. Census or tabulated valuation data.
   - Purpose: active headcount and salary by age, actual service, credited
     service, contribution design, hire date, elected-official status, and
     employer group.
   - Likely source: not fully public; request from APERS or reconstruct from
     valuation and ACFR schedules if only aggregate modeling is possible.

## Required Data Elements By Category

### Plan Provisions

Collect for each plan:

- plan id and plan description
- membership classes and subgroups
- employer groups
- tier and hire-cohort definitions
- vesting requirements
- normal retirement eligibility
- early retirement eligibility
- early retirement reduction formulas or tables
- final average compensation windows
- benefit multipliers
- COLA rules
- member contribution rates
- employer contribution rates
- compensation caps and pensionable-pay definitions
- DROP eligibility and account behavior
- refund rules
- deferred vested rules
- restoration or repayment rules
- disability and survivor provisions if in scope

Alabama-specific provisions:

- Tier 1 versus Tier 2 ERS provisions
- state employee, state police, and local employee distinctions
- local employer option flags
- local employer 25-year retirement treatment
- employer elections under Act 2022-348
- compensation caps tied to base pay
- Tier 1-only or closed legacy DROP treatment

APERS-specific provisions:

- contributory versus non-contributory service treatment
- service-period multipliers
- actual service versus credited service
- hours-to-service conversion rules
- county and municipal elected official enhanced credit
- pre/post July 1, 2022 FAC and COLA treatment
- active APERS DROP rules
- PAW, refund, and repayment provisions

### Demographics

Collect or derive:

- active headcount by age and service
- active average salary by age and service
- active payroll by class, tier, and employer group
- retiree count by age
- retiree average benefit by age
- retiree total annual benefit by age
- deferred vested count and estimated allowances
- refund-eligible inactive counts if available
- entrant age distribution
- entrant salary distribution

For Alabama, split demographics by:

- state employees
- state police
- local employees
- Tier 1 and Tier 2
- employer election group where available
- firefighter, law enforcement, corrections, or other special subgroups where
  applicable

For APERS, split demographics by:

- actual service
- credited service
- contribution design
- hire cohort
- elected official status
- employer group
- DROP status where available

### Decrements

Collect or derive:

- termination rates
- retirement rates
- early retirement rates
- DROP entry rates if modeled explicitly
- disability rates if modeled
- refund election rates if modeled
- deferred vested commencement assumptions
- restoration or repayment assumptions if modeled

For Alabama, decrement tables should distinguish local employer options when
those options materially affect eligibility.

For APERS, decrement tables should distinguish actual-service and
credited-service thresholds where plan behavior depends on both ledgers.

### Mortality

Collect:

- base mortality tables
- mortality improvement scale
- active mortality assumptions
- retiree mortality assumptions
- disabled mortality assumptions if modeled
- class-specific mortality basis, such as general, safety, teacher, or other
  published tables

If the plan valuation uses a standard table such as Pub-2010 with an
improvement scale, convert it to the repo's `base_rates.csv` and
`improvement_scale.csv` shape.

### Funding

Collect:

- actuarial value of assets
- market value of assets
- actuarial accrued liability
- unfunded actuarial accrued liability
- normal cost
- employee contributions
- employer contributions
- benefit payments
- refunds
- administrative expenses if used in contribution rates
- amortization bases
- amortization periods
- payroll growth assumption
- investment return assumption
- asset smoothing method
- funding policy
- employer contribution policy
- statutory contribution schedules

For Alabama, collect separate state employee, state police, and local employer
funding results where available.

For APERS, collect employer group contribution rates and any special rates for
wildlife officers, civilian firefighters, district judges, or other groups
called out by APERS.

### Calibration Targets

Collect targets for model calibration and validation:

- total active members
- total covered payroll
- retiree population
- total annual benefits
- average benefit
- deferred vested counts
- estimated deferred allowances
- total AAL
- AAL by group if available
- normal cost rate
- employer contribution rate
- employee contribution rate
- funded ratio
- AVA and MVA
- first-year projected benefit payments
- first-year projected refunds
- amortization payment or UAAL contribution component

Calibration targets should be recorded with:

- source document name
- source document date
- valuation date
- fiscal year
- page or table reference
- extraction notes
- whether the value is directly published or derived

## Public Report Data Versus Request-Based Data

Public reports are usually enough for:

- aggregate plan provisions
- contribution rates
- high-level assets and liabilities
- total active counts and payroll
- total retiree counts and benefit payments
- aggregate deferred vested counts
- valuation assumptions and methods
- broad membership schedules
- investment return and funding policy data

Public reports may be insufficient for:

- age-service-salary grids
- class-specific salary distributions
- member-level hire dates
- employer-option flags by member
- Alabama local employer election status by member
- APERS actual service and credited service by member
- APERS service segments by contribution design
- elected official enhanced credit history
- DROP entry cohorts and frozen benefit details
- refund/restoration history

If full census data is unavailable, build a documented aggregate model using
published schedules and record the approximation explicitly in the plan config
or extraction notes.

## Extraction Notes To Maintain

For each collected document, create or maintain extraction notes with:

- source URL
- download date
- document title
- valuation date or fiscal year
- plan population covered
- tables used
- fields extracted
- transformations applied
- assumptions made
- known gaps
- reviewer/date

Recommended location:

- `plans/{plan}/source_notes/`

Recommended files:

- `plans/{plan}/source_notes/source_inventory.md`
- `plans/{plan}/source_notes/extraction_notes.md`
- `plans/{plan}/source_notes/data_gaps.md`

## Minimum Collection Checklist

Minimum Alabama ERS collection before implementation:

- ERS member handbook
- latest ERS actuarial valuation report
- latest RSA ACFR
- Act 2022-348 employer election material
- local employer rate or option documentation
- mortality and assumption details from valuation or experience study
- active and retiree demographic schedules
- funding inputs and calibration targets

Minimum Arkansas APERS collection before implementation:

- APERS member handbook
- latest APERS actuarial valuation report
- latest APERS ACFR
- employer reporting specifications and samples
- employer and member contribution rate publications
- mortality and assumption details from valuation or experience study
- active and retiree demographic schedules
- funding inputs and calibration targets

## Assumptions

- Data collection is separate from resolver architecture.
- The original context document remains unchanged.
- Public reports are acceptable for a first aggregate model, but census or
  detailed valuation data is preferred for production-grade plan modeling.
- Source documents should be rechecked before extraction because plan
  provisions, rates, and report URLs can change.
- Any value derived from a report table must be marked as derived rather than
  directly published.
