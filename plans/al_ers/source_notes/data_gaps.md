# Alabama ERS Data Gaps

Collection date: 2026-04-28

The public valuation and handbook support a first aggregate model, but they do
not support a production-grade member-flow model without additional data.

## Must-Have But Unavailable From Public Sources

| Data need | Why it is must-have | Public substitute available | Gap severity |
| --- | --- | --- | --- |
| Active headcount and payroll by exact age, service, tier, FLC/non-FLC, State/State Police/local group, and local employer option | Required to build `*_headcount.csv` and `*_salary.csv` without synthetic allocation | Valuation Table 1 gives counts and payroll by group/tier/FLC only | High |
| Local employer-specific rate schedule and local funding results | Local contribution rates and amortization periods vary by employer and benefit option | Valuation says local FY2027 rates will be submitted separately; employer page has state-only rate schedule | High |
| Local employer Act 2022-348 election flags and effective dates by employer | Required to model local employers that provide Tier 1 benefits to Tier 2 members | Employer page links to adopted-agency material, but member-level/employer-level modeling fields were not collected | High |
| Local 25-year agency adoption flags by employer and member | Retirement eligibility differs for 25-year agencies | Handbook describes 25-year and non-25-year treatment, but no complete employer-member crosswalk was found | High |
| Complete decrement tables in machine-readable form | Required for `termination_rates.csv` and `retirement_rates.csv` by class | Valuation Schedule D has assumption tables and representative values; full model-shaped tables still need digitization and QA | High |
| Base Pub-2010 mortality rates and MP-2020 improvement scale in repo CSV shape | Required for `base_rates.csv` and `improvement_scale.csv` | Valuation describes table basis, adjustments, and improvement scale | High |
| Retiree count and annual benefit by age | Required for `retiree_distribution.csv` | Valuation provides total retirees and annual allowances by group only | High |
| Deferred vested members by age and estimated allowance | Needed for deferred-liability and commencement calibration | Valuation provides total deferred vested count and allowance by group | Medium |
| Entrant age and entrant salary profile | Needed for open-group projection after initial valuation | Not public in collected sources | Medium |
| DROP participant counts, entry cohorts, account balances, and payout elections | Needed if DROP is modeled explicitly | Valuation provides post-DROP active counts and total DROP distributions only | Medium |
| State Police handbook provisions | Required for precise State Police Tier 1/Tier 2 benefit rules | ERS publications page identifies State Police handbooks, but this pass extracted the general ERS handbook and valuation only | Medium |
| Compensation cap detail by fiscal year | Needed for pensionable-pay projection and validation | Handbook gives 120% Tier 1 and 125% Tier 2 base-pay caps; employer page links annual earnable-compensation limits | Medium |
| Disability and survivor election history | Needed for full benefit-state modeling | Valuation gives broad assumptions and aggregate outcomes | Low to medium |

## Public But Not Yet Digitized

- Alabama ERS valuation Schedule D decrement assumptions.
- Alabama ERS valuation Schedule G amortization bases.
- Alabama ERS GASB 67/68 schedules for 9/30/2025.
- RSA Annual Report 2025 investment and financial statement schedules.
- ERS State Police Tier 1 and Tier 2 handbooks from the ERS publications page.

## Recommended Requests To RSA

1. Anonymized valuation census extract with age, service, pay, tier, class,
   FLC flag, State/State Police/local group, employer id, local benefit-option
   flags, and DROP status.
2. Retiree census or tabulation by age, benefit amount, benefit type, option,
   DROP status, and group.
3. Deferred vested and inactive census by age, service, contribution balance,
   estimated benefit, and expected commencement age.
4. Complete local employer rate report for fiscal years beginning October 1,
   2025 and October 1, 2026.
5. Act 2022-348 and local 25-year retirement election files by employer and
   effective date.
6. Experience study or full assumption workbook behind the valuation tables.
7. Machine-readable mortality table adjustments or confirmation to use SOA
   Pub-2010 base tables with the valuation adjustments and MP-2020 scale.

