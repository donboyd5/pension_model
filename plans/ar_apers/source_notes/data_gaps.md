# Arkansas APERS Data Gaps

Collection date: 2026-04-28

The public valuation and handbook support a first aggregate model, and APERS
publishes more usable demographic schedules than Alabama ERS. A production-grade
projection still needs data that is not public in the collected sources.

## Must-Have But Unavailable From Public Sources

| Data need | Why it is must-have | Public substitute available | Gap severity |
| --- | --- | --- | --- |
| Active census split by actual service, credited service, contribution design, hire date, elected-official status, employer group, and DROP status | APERS eligibility and benefits depend on actual service, credited service, contributory status, hire cohort, and enhanced elected-official credit | Valuation includes aggregate active counts/payroll by attained age and service and total active payroll | High |
| Service-segment history by member or group | Multipliers differ by non-contributory vs contributory and pre/post July 1, 2007 service | Handbook gives segment multipliers; public reports do not provide segment balances | High |
| Hire cohort split around July 1, 2022 | FAC and COLA rules depend on first employment before/on-after July 1, 2022 | Handbook gives rules; valuation does not publish a cohort cross-tab | High |
| Full age-service-salary grid by contribution design and employer group | Required to build separate model classes without synthetic allocation | Valuation has an active age-service count/payroll grid for State and Local Division, but not by all modeling dimensions | High |
| Complete retirement, withdrawal, disability, and death rates in machine-readable format | Required for decrement input CSVs | Valuation has public assumption tables and actual-vs-expected schedules; full digitization and QA still needed | High |
| Base Pub-2010 mortality rates and MP-2021 improvement scale in repo CSV shape | Required for `base_rates.csv` and `improvement_scale.csv` | Valuation describes table basis and percentages | High |
| DROP account balances, entry cohorts, expected duration distribution, and payout elections | Needed if DROP is modeled explicitly beyond aggregate payroll and liability loads | Handbook and valuation give eligibility, crediting rate, duration cap, and reported DROP/returned-retiree payroll | Medium |
| Member-level or employer-level elected official enhanced credit history | Enhanced service and additional contributions require elected-official status and start date | Handbook and employer page give rules and additional contribution rates | Medium |
| Employer reporting work-report import samples and data dictionary, fully archived | Useful to map employer files to model fields | Employer reporting page links design specifications and samples; this pass did not download them | Medium |
| FY2025 ACFR | Useful for final audited financial statement reconciliation | FY2024 ACFR is latest listed on public APERS reports/publications pages; FY2025 valuation provides current funding values | Low to medium |
| Experience Study dated May 10, 2023 | Needed to validate complete decrement basis and any smoothing/credibility choices | Valuation cites it and includes assumption tables; standalone report was not collected in this pass | Medium |

## Public But Not Yet Digitized

- Active members by attained age and years of service from the June 30, 2025
  valuation, pages B-17 and following.
- APERS retirement assumption tables, pages E-4 through E-6.
- APERS separation, death, disability, and pay-increase assumptions, pages E-7
  and E-8.
- Salary increase actual-vs-expected schedule, pages C-13 and following.
- APERS employer reporting import specifications and samples linked from the
  employer reporting page.
- APERS Funding Policy linked from the Board of Trustees page.

## Recommended Requests To APERS

1. Anonymized valuation census extract with date of birth, gender, actual
   service, credited service, pay, contribution design, hire date, employer
   group, elected-official status, enhanced service, reciprocal service, and
   DROP status.
2. Service-segment extract or tabulation splitting service by non-contributory,
   contributory, pre-July 1 2007, post-July 1 2007, elected official enhanced
   credit, and reciprocal service.
3. Retiree census or tabulation by age, benefit amount, benefit type, option,
   COLA cohort, DROP status, and employer group.
4. DROP participant file with entry date, service at entry, frozen benefit,
   account balance, interest credits, and elected payout form.
5. Complete assumption workbook or machine-readable tables from the 2023
   experience study.
6. Employer reporting specifications and samples if the system will ingest
   employer-submitted work reports directly.
7. Machine-readable mortality table adjustments or confirmation to use SOA
   Pub-2010 base tables with the valuation percentages and MP-2021 scale.

