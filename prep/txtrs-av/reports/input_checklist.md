# TXTRS-AV Input Checklist

Plan-level view of every input the runtime needs to run `txtrs-av`, with status and source for each. Generated from `prep/txtrs-av/input_checklist.csv` by `prep/common/render_input_checklist.py`. Schema is documented in `prep/common/reports/input_checklist_README.md`.

## Status summary

| status | count |
| --- | --- |
| have | 70 |
| partial | 11 |
| missing | 0 |
| N/A | 14 |
| **total** | **95** |

## Open gaps

Rows with status `missing` or `partial`.

| category | item | status | source_type | notes |
| --- | --- | --- | --- | --- |
| decrements | retirement_rates | partial | AV-derived | Verified 2026-05-01: Normal retirement rates published M/F separately for ages 50-64; runtime accepts a single schedule so build uses arithmetic average — e.g., age 50 = (0.110+0.106)/2 = 0.108; age 60 = (0.150+0.178)/2 = 0.164; age 75+ = (1.000+1.000)/2 = 1.000. AV bands 65-69, 70-74, 75+ are expanded to single ages and carried flat through max_age=120. Early retirement rates are M/F-identical in source (45-59 = 0.006; 60-64 = 0.010-0.050); transcribed exactly. Status partial: M/F averaging is a known runtime-architecture simplification (one schedule). |
| demographics | retiree_distribution | partial | AV-derived | Verified 2026-05-01: 66 single-age rows (55-120). AV pre-retirement bands (Up to 35, 35-40, 40-44, 45-49, 50-54, 55-59) bunched into canonical ages 55-59 (sum 33,457 / 5 ages = 6,691.4 each, total benefit $1,274,286,122 / 5 = $254,857,224.4 each). 60-64..95-99 bands spread evenly across their 5-year ranges. "100 & up" (335 retirees, $7,073,777) spread evenly across ages 100-120 (21 ages × 15.95238 ≈ 335). Total CSV count 475,891 matches AV Table 18 grand total exactly. Status partial: life annuities only — disabled annuities (Table 19, 12,030) and survivor annuities (Table 15b, 18,291) deferred per issue #71. |
| funding_policy | ava_smoothing_recognition_period | partial | AV-derived | DIVERGENCE: AV specifies 5-year phase-in ("five-year phase-in...minimum rate of 20% per year"). Config has 4 and the model architecture is hardcoded for 4-year phasing (4 deferral buckets in src/pension_model/core/_funding_helpers.py with fractions 3/4, 2/3, 1/2 = 25%/year recognition over 4 years). Setting the config to 5 will not match the AV without model code changes (5th bucket + 1/5 fractions). See phase-anytime issue and phase-post-r generalization issue. |
| funding_policy | funding_lag | partial | source-unverified | Searched cert letter and Appendix 2 on 2026-05-01. AV does not state a "1-year lag" directly. AV does say "the next opportunity there is to change the contribution rate, which in this case would be September 1, 2025 following the 2025 legislative session" — consistent with a ~1-year gap between valuation cert (Nov 2024) and next rate-change opportunity (Sep 2025), but not a direct statement of the funding_lag parameter. Likely reflects TX legislative cycle / state FY timing as a modeling convention. |
| funding_year0 | defer_y1_legacy | partial | AV-derived | AV publishes one aggregate remaining deferral; per-year split is reconstructed. Only y2 is populated; y1/y3/y4 set to 0. |
| funding_year0 | defer_y2_legacy | partial | AV-derived | Carries the full aggregate remaining deferral per source_notes funding_note |
| funding_year0 | defer_y3_legacy | partial | AV-derived | Set to 0 — published aggregate not split by year |
| funding_year0 | defer_y4_legacy | partial | AV-derived | Set to 0 — published aggregate not split by year |
| mortality | base_rates | partial | estimated | Inspected 2026-05-01: 412 rows = 103 ages (18-120) × 2 genders × 2 member_types (employee, retiree). Active (employee) qx values are clean round numbers consistent with PubT-2010(B) Teacher Below-Median Income source-direct (e.g., male 50 = 0.00149, female 50 = 0.00093). Retiree qx values are spline-fitted estimator output (e.g., male 50 = 0.00207, female 50 = 0.00127). Status partial per issues #72 (AV-named 2021 TRS Healthy Pensioner table not public; fallback estimator used) and #73 (active improvement scale choice). |
| term_vested | avg_deferral_years | partial | estimated | Estimated D = distribution age (~62, weighted across tiers per Appendix 1 plan provisions) − avg current age (~50, inferred since AV does not publish inactive-vested age distribution). AV Table 15a publishes inactive vested counts (138,146) and contributions ($5.305B) but no age distribution. Working estimate D = 12; documented in prep/txtrs-av/methods/term_vested_deferred_annuity.md. Refinement requires inactive-vested age distribution from TRS member statistical reports or external data. |
| term_vested | avg_payout_years | partial | estimated | Estimated L = approximate remaining life expectancy at distribution age 62 under the AV's post-retirement mortality basis (2021 TRS of Texas Healthy Pensioner Mortality Tables + Scale UMP 2021 immediate convergence). Typical life expectancy at age 62 under such a table is ~24-26 years; L = 25 is a midpoint estimate. Refinement: compute survival-weighted annuity factor at 62 directly from plans/txtrs-av/data/mortality/base_rates.csv. See phase-anytime issue. |

## Full checklist by category

### Plan meta

| item | required | status | source_type | source citation | notes |
| --- | --- | --- | --- | --- | --- |
| data_dir | required | have | runtime-only | — | Wiring / file path — not subject to provenance review. Typically derivable from plan_name. |
| plan_description | required | have | runtime-only | — | Metadata / human label — not subject to provenance review. |
| plan_name | required | have | runtime-only | — | Metadata / identifier — not subject to provenance review. |

### Economic assumptions

| item | required | status | source_type | source citation | notes |
| --- | --- | --- | --- | --- | --- |
| dr_current | required | have | AV-direct | AV_2024; printed p. 60 / PDF p. 67; Appendix 2 §1 Investment Return Rate | Verified 2026-05-01: "Investment Return Rate 7.00% per annum, compounded annually, composed of an assumed 2.30% inflation rate and a 4.70% real rate of return, net of investment expenses." |
| dr_new | required | have | AV-direct | AV_2024; printed p. 60 / PDF p. 67; Appendix 2 §1 Investment Return Rate | Verified 2026-05-01: AV cites a single 7.00% investment return rate; we apply the same rate to new entrants as a modeling default consistent with US public-pension convention. |
| dr_old | required | have | AV-direct | AV_2024; printed p. 60 / PDF p. 67; Appendix 2 §1 Investment Return Rate | Verified 2026-05-01: 7.00% AV investment return rate. Used by the cashflow-estimation pathway anchored to the published-rate quantity. |
| inflation | required | have | AV-direct | AV_2024; printed p. 60 / PDF p. 67; Appendix 2 §1 Investment Return Rate | Verified 2026-05-01: AV §1 cites "an assumed 2.30% inflation rate" as a component of the 7.00% return. Same 2.30% inflation appears in §3 Rates of Salary Increase and in the PAYROLL GROWTH section. |
| model_return | required | have | AV-direct | AV_2024; printed p. 60 / PDF p. 67; Appendix 2 §1 Investment Return Rate | Verified 2026-05-01: 7.00% AV investment return rate. Equal to dr_current by US public-pension convention. |
| payroll_growth | required | have | AV-direct | AV_2024; printed p. 66 / PDF p. 73; Appendix 2 §PAYROLL GROWTH FOR FUNDING OF UNFUNDED ACTUARIAL ACCRUED LIABILITY | Verified 2026-05-01: "Total payroll is expected to grow at 2.90% per year. The total general wage increase assumption of 2.90% is made up of an inflation rate of 2.30% plus a 0.60% real wage growth." Distinct from individual-member salary growth tail (2.95% = 2.30% inflation + 0.65% productivity, p. 63 / PDF 70). |
| pop_growth | optional | N/A | runtime-only | — | Not used in txtrs-av config |

### Ranges (modeling grid)

| item | required | status | source_type | source citation | notes |
| --- | --- | --- | --- | --- | --- |
| max_age | required | have | runtime-only | — |  |
| max_yos | required | have | runtime-only | — |  |
| min_age | required | have | runtime-only | — |  |
| min_entry_year | required | have | runtime-only | — |  |
| model_period | required | have | runtime-only | — |  |
| new_year | required | have | runtime-only | — |  |
| start_year | required | have | AV-direct | AV_2024; Title page | 2024 |

### Benefit rules

| item | required | status | source_type | source citation | notes |
| --- | --- | --- | --- | --- | --- |
| benefit_types | required | have | AV-direct | AV_2024; Plan provisions | DB only |
| cola_block | required | have | AV-direct | AV_2024; printed p. 46 / PDF p. 53; Appendix 1 sections A-E (silence on automatic COLA); H, I (historical ad hoc COLAs); cert letter p. 3 / PDF p. 4 (2023 ad hoc COLA already paid) | Verified 2026-05-01: TX TRS has no automatic ongoing COLA. Appendix 1 mentions only historical ad hoc COLAs (1991, 1993 Legislatures) and the 88th Legislature 2023 one-time COLA already paid in FY 2024 and reflected in the 2024 AAL. All cola.*_active = 0.0 and current_retire = 0.0 are AV-supported by silence on automatic COLA. |
| db_ee_cont_rate | required | have | AV-direct | AV_2024; printed p. 53 / PDF p. 60; Appendix 1 Section F — MEMBER CONTRIBUTIONS | Verified 2026-05-01 against AV: Appendix 1 F states "8.25% for Fiscal Years on and after 2024." Cert letter on printed p. 3 / PDF p. 4 corroborates: "member contribution rate has increased from 7.70% to the current 8.25% in Fiscal Year 2024." Statutory phase-in (2019 Legislature) completed FY 2025. |
| db_ee_interest_rate | required | have | plan-admin-direct | BENEFITS_HANDBOOK; printed p. 7 / PDF p. 10; Member Contribution Account — Interest Earned | Verified 2026-05-01: "Interest on your contributions is currently calculated at the rate of 2% a year. TRS credits interest on Aug. 31 of each year." Also published on https://www.trs.texas.gov/pension-benefits/know-benefits/understand-benefits/member-contributions: "Keep in mind, your contributions continue to earn 2% interest per year." The AV does not restate this rate; statute delegates the rate to the TRS Board, which has set it at 2%. Searched AV Appendix 1 (printed pp. 46-53) and Appendix 2 §1-4 (printed pp. 60-66); only 5%/year on DROP accounts is mentioned in the AV (Appendix 1 A.6 b.5). |
| fas_years_default | required | have | AV-direct | AV_2024; printed p. 46 / PDF p. 53; Appendix 1 Section A.2 — Standard Annuity | Verified 2026-05-01: "average of the highest five annual salaries (based on creditable compensation)." Default applies to non-grandfathered members. |
| fas_years_grandfathered | conditional | have | AV-direct | AV_2024; printed p. 46 / PDF p. 53; Appendix 1 Section A.2 — Standard Annuity | Verified 2026-05-01: "Members who as of August 31, 2005, were either age 50, had 25 years of service, or whose age plus service totaled 70 have their standard annuity calculated using the average of their highest three annual salaries." |
| min_benefit_monthly | optional | have | AV-direct | AV_2024; printed p. 46 / PDF p. 53; Appendix 1 Section A.2 — Normal Retirement Benefits | Verified 2026-05-01: "Greater of standard annuity, or $150 per month." |
| cash_balance_block | conditional | N/A | — | — | DB-only plan |
| dc_block | conditional | N/A | — | — | DB-only plan |
| retire_refund_ratio | optional | N/A | — | — | Omitted from txtrs-av per source_notes |

### Plan structure (classes, tiers, multipliers)

| item | required | status | source_type | source citation | notes |
| --- | --- | --- | --- | --- | --- |
| benefit_multipliers | required | have | AV-direct | AV_2024; printed p. 46 / PDF p. 53; Appendix 1 Section A.2 — Standard Annuity | Verified 2026-05-01: "The product of 2.3% of the member's average compensation multiplied by years of creditable service." Flat 2.3% applies all tiers. |
| class_groups | required | have | runtime-only | — |  |
| classes | required | have | AV-direct | AV_2024; Plan provisions | Single class "all" |
| plan_design | required | have | runtime-only | — | DB-only |
| tiers | required | have | AV-direct | AV_2024; Plan provisions; Appendix 1 | 4 tiers: grandfathered, pre_2007, vested_2014, current. vested_2014 boundary is approximated by entry year per tier_encoding_note in plan_config |

### Funding policy

| item | required | status | source_type | source citation | notes |
| --- | --- | --- | --- | --- | --- |
| ava_smoothing_recognition_period | required | partial | AV-derived | AV_2024; printed p. 67 / PDF p. 74; Appendix 2 §ACTUARIAL VALUE OF ASSETS | DIVERGENCE: AV specifies 5-year phase-in ("five-year phase-in...minimum rate of 20% per year"). Config has 4 and the model architecture is hardcoded for 4-year phasing (4 deferral buckets in src/pension_model/core/_funding_helpers.py with fractions 3/4, 2/3, 1/2 = 25%/year recognition over 4 years). Setting the config to 5 will not match the AV without model code changes (5th bucket + 1/5 fractions). See phase-anytime issue and phase-post-r generalization issue. |
| funding_lag | required | partial | source-unverified | AV_2024; printed p. 68 / PDF p. 75; Appendix 2 §REASONABLE ACTUARIALLY DETERMINED CONTRIBUTION (ADC) PER ASOP 4 | Searched cert letter and Appendix 2 on 2026-05-01. AV does not state a "1-year lag" directly. AV does say "the next opportunity there is to change the contribution rate, which in this case would be September 1, 2025 following the 2025 legislative session" — consistent with a ~1-year gap between valuation cert (Nov 2024) and next rate-change opportunity (Sep 2025), but not a direct statement of the funding_lag parameter. Likely reflects TX legislative cycle / state FY timing as a modeling convention. |
| amo_method | required | have | AV-direct | AV_2024; printed p. 68 / PDF p. 75; Appendix 2 §ACTUARIALLY DETERMINED EMPLOYER CONTRIBUTION (ADEC) | Verified 2026-05-01: "The ADEC is determined as the level percentage of payroll that will cover the Fund's normal cost and amortize the Fund's unfunded liabilities..." Cost method is Entry Age Normal (same section). |
| amo_pay_growth | required | have | AV-direct | AV_2024; printed p. 66 / PDF p. 73; Appendix 2 §PAYROLL GROWTH FOR FUNDING OF UNFUNDED ACTUARIAL ACCRUED LIABILITY | Verified 2026-05-01: same 2.90% payroll growth assumption used for UAAL amortization. |
| amo_period_current | required | have | AV-direct | AV_2024; Funding policy | 28 years |
| amo_period_new | required | have | AV-direct | AV_2024; printed p. 68 / PDF p. 75; Appendix 2 §ACTUARIALLY DETERMINED EMPLOYER CONTRIBUTION (ADEC) | Verified 2026-05-01: "...if the fixed rate contributions produce a funding period in excess of 30 years then a 30-year amortization period is used." The AV uses one amortization stream; the model applies the 30-year cap as the period for new gain/loss layers added after the valuation date. Modeling convention consistent with the AV's stated 30-year cap. |
| ava_smoothing_method | required | have | AV-direct | AV_2024; printed p. 67 / PDF p. 74; Appendix 2 §ACTUARIAL VALUE OF ASSETS | Verified 2026-05-01: "The actuarial value of assets is equal to the market value of assets less a five-year phase-in of the excess/(shortfall) between expected investment return and actual income." Method is gain/loss style — recognizes the difference between actual and expected returns over a phase-in period. |
| policy | required | have | AV-direct | AV_2024; printed p. 3 / PDF p. 4; Cert letter §FINANCING OBJECTIVE OF THE PLAN; Appendix 2 §ACTUARIAL COST METHOD (printed p. 68 / PDF p. 75) | Verified 2026-05-01: "The employee, employer, and State contribution rates are established by State law..." Cert letter and §ACTUARIAL COST METHOD both confirm rates set by statute / Legislative appropriation. |
| statutory_ee_rate_schedule | conditional | have | AV-direct | AV_2024; Funding policy |  |
| statutory_er_rate_components | conditional | have | AV-direct | AV_2024; Funding policy | Includes public-edu surcharge |

### Valuation inputs (per class)

| item | required | status | source_type | source citation | notes |
| --- | --- | --- | --- | --- | --- |
| ben_payment | required | have | AV-direct | AV_2024; printed p. 17 / PDF p. 24; Table 2 Summary of Cost Items | $15.258B |
| er_dc_cont_rate | conditional | have | AV-direct | AV_2024; N/A — DB-only | 0.0 |
| retiree_pop | required | have | AV-direct | AV_2024; printed p. 17 / PDF p. 24; Table 2 | 508701 |
| total_active_member | required | have | AV-direct | AV_2024; printed p. 17 / PDF p. 24; Table 2 | 970872 |
| val_aal | required | have | AV-direct | AV_2024; printed p. 17 / PDF p. 24; Table 2 | $273.095B |
| val_norm_cost | required | have | AV-direct | AV_2024; printed p. 17 / PDF p. 24; Table 2 | 12.1% |
| val_payroll | optional | have | AV-direct | AV_2024; printed p. 19 / PDF p. 26; Table 3b ESTIMATION OF COVERED PAYROLL AND EFFECTIVE EMPLOYER CONTRIBUTION RATES, row 1d | Verified 2026-05-01: "Projected Covered Payroll for Next Fiscal Year (1c increased by one year's payroll growth)" = $61,388,248,000. Matches init_funding.csv:total_payroll. Used as out-of-sample comparison target in calibration diagnostics (src/pension_model/core/calibration.py model_payroll vs val_payroll). |
| headcount_group | optional | N/A | runtime-only | — | Single-class plan |

### Funding year-0 seed (init_funding.csv)

| item | required | status | source_type | source citation | notes |
| --- | --- | --- | --- | --- | --- |
| defer_y1_legacy | required | partial | AV-derived | AV_2024; printed p. 20 / PDF p. 27; Table 4 | AV publishes one aggregate remaining deferral; per-year split is reconstructed. Only y2 is populated; y1/y3/y4 set to 0. |
| defer_y2_legacy | required | partial | AV-derived | AV_2024; printed p. 20 / PDF p. 27; Table 4 | Carries the full aggregate remaining deferral per source_notes funding_note |
| defer_y3_legacy | required | partial | AV-derived | AV_2024; printed p. 20 / PDF p. 27; Table 4 | Set to 0 — published aggregate not split by year |
| defer_y4_legacy | required | partial | AV-derived | AV_2024; printed p. 20 / PDF p. 27; Table 4 | Set to 0 — published aggregate not split by year |
| aal_legacy | required | have | AV-direct | AV_2024; printed p. 17 / PDF p. 24; Table 2 | Equals total_aal in single-tier plan |
| admin_exp_rate | required | have | AV-direct | AV_2024; printed p. 17 / PDF p. 24; Table 2 | 0.14% |
| ava_legacy | required | have | AV-direct | AV_2024; printed p. 17 / PDF p. 24; Table 2 |  |
| mva_legacy | required | have | AV-direct | AV_2024; printed p. 20 / PDF p. 27; Table 4 |  |
| total_aal | required | have | AV-direct | AV_2024; printed p. 17 / PDF p. 24; Table 2 |  |
| total_ava | required | have | AV-direct | AV_2024; printed p. 17 / PDF p. 24; Table 2 |  |
| total_mva | required | have | AV-direct | AV_2024; printed p. 20 / PDF p. 27; Table 4 Development of Actuarial Value of Assets |  |
| total_payroll | required | have | AV-direct | AV_2024; printed p. 17 / PDF p. 24; Table 2 |  |
| year | required | have | AV-direct | AV_2024; Title page | 2024 |
| aal_new | conditional | N/A | — | — | Zero — no new tier at year 0 |
| ava_new | conditional | N/A | — | — |  |
| defer_y1_new | conditional | N/A | — | — |  |
| defer_y2_new | conditional | N/A | — | — |  |
| defer_y3_new | conditional | N/A | — | — |  |
| defer_y4_new | conditional | N/A | — | — |  |
| mva_new | conditional | N/A | — | — |  |

### Calibration (computed)

| item | required | status | source_type | source citation | notes |
| --- | --- | --- | --- | --- | --- |
| cal_factor | required | have | computed | — | 1.0 in txtrs-av |
| nc_cal | required | have | computed | — | Computed by pension-model calibrate |
| pvfb_term_current | required | have | computed | — | Single-class plug absorbs per-bucket gaps; issue #48 |

### Term-vested cashflow parameters

| item | required | status | source_type | source citation | notes |
| --- | --- | --- | --- | --- | --- |
| avg_deferral_years | required | partial | estimated | AV_2024; printed p. 66 / PDF p. 73; Appendix 2 §BENEFIT ELECTION OF VESTED TERMINATING MEMBERS (printed p. 66 / PDF p. 73); Appendix 1 §A.2 Normal Retirement (printed p. 46 / PDF p. 53); Table 15a (printed p. 38 / PDF p. 45) | Estimated D = distribution age (~62, weighted across tiers per Appendix 1 plan provisions) − avg current age (~50, inferred since AV does not publish inactive-vested age distribution). AV Table 15a publishes inactive vested counts (138,146) and contributions ($5.305B) but no age distribution. Working estimate D = 12; documented in prep/txtrs-av/methods/term_vested_deferred_annuity.md. Refinement requires inactive-vested age distribution from TRS member statistical reports or external data. |
| avg_payout_years | required | partial | estimated | AV_2024; printed p. 64 / PDF p. 71; Appendix 2 §4 Post-retirement Mortality (printed p. 64 / PDF p. 71) | Estimated L = approximate remaining life expectancy at distribution age 62 under the AV's post-retirement mortality basis (2021 TRS of Texas Healthy Pensioner Mortality Tables + Scale UMP 2021 immediate convergence). Typical life expectancy at age 62 under such a table is ~24-26 years; L = 25 is a midpoint estimate. Refinement: compute survival-weighted annuity factor at 62 directly from plans/txtrs-av/data/mortality/base_rates.csv. See phase-anytime issue. |
| method | required | have | runtime-only | — | deferred_annuity |

### Demographics

| item | required | status | source_type | source citation | notes |
| --- | --- | --- | --- | --- | --- |
| retiree_distribution | required | partial | AV-derived | AV_2024; printed p. 42 / PDF p. 49; Table 18 Distribution of Life Annuities by Age | Verified 2026-05-01: 66 single-age rows (55-120). AV pre-retirement bands (Up to 35, 35-40, 40-44, 45-49, 50-54, 55-59) bunched into canonical ages 55-59 (sum 33,457 / 5 ages = 6,691.4 each, total benefit $1,274,286,122 / 5 = $254,857,224.4 each). 60-64..95-99 bands spread evenly across their 5-year ranges. "100 & up" (335 retirees, $7,073,777) spread evenly across ages 100-120 (21 ages × 15.95238 ≈ 335). Total CSV count 475,891 matches AV Table 18 grand total exactly. Status partial: life annuities only — disabled annuities (Table 19, 12,030) and survivor annuities (Table 15b, 18,291) deferred per issue #71. |
| active_headcount | required | have | AV-derived | AV_2024; printed p. 41 / PDF p. 48; Table 17 Distribution of Active Members by Age and Service | Verified 2026-05-01: 59 rows = 10 canonical ages × 8 canonical YOS (skip-zero). AV age bands (Under 25 .. 65+) → canonical age midpoints (22, 27, ..., 67). AV single-year YOS columns 0-3 collapsed into canonical yos=2; AV bands 4, 5-9, 10-14, ..., 35-39 → canonical YOS 7, 12, ..., 37. Spot-checked: age 22/yos 2 count = 17,422+8,195+2,700+695 = 29,012; age 27/yos 2 = 73,280; age 27/yos 12 = 90. Total CSV count 970,872 matches AV Table 17 grand total exactly. Build script: scripts/build/build_txtrs_av_from_av.py:152-193. |
| active_salary | required | have | AV-derived | AV_2024; printed p. 41 / PDF p. 48; Table 17 Distribution of Active Members by Age and Service | Verified 2026-05-01: same canonical grid as all_headcount. For canonical yos=2 (collapsed from AV YOS 0-3), salary is count-weighted average across the four early columns. Spot-checked: age 22/yos 2 salary = (17422×31032 + 8195×37619 + 2700×34062 + 695×32962) / 29012 = 33,220.85; age 27/yos 2 = 47,906.96 — both match CSV exactly. For later canonical YOS (7, 12, ..., 37), salary is taken directly from the corresponding AV band. Build script: scripts/build/build_txtrs_av_from_av.py:152-193. |
| entrant_profile | optional | have | AV-derived | AV_2024; printed p. 69 / PDF p. 76; Appendix 2 NEW ENTRANT PROFILE | Verified 2026-05-01: 10 canonical entry ages (20, 25, ..., 65). Counts use boundary-merge rule (canonical 20 = bands [15-19]+[20-24]; canonical 65 = bands [60-64]+[65-69]; others = single band). Salaries use adjacent-band-average rule. Build sums to 442,932 (counts 20-24 in both canonical 20 and 25). Spot-checked: canonical 20 salary = (25,003+47,410)/2 = 36,206.5; canonical 30 share = 85,761/442,932 = 0.19362. Build script: scripts/build/build_txtrs_av_from_av.py:230-289. |
| salary_growth | required | have | AV-direct | AV_2024; printed p. 63 / PDF p. 70; Appendix 2 §3 Rates of Salary Increase | Verified 2026-05-01: AV publishes Total = inflation 2.30% + productivity 0.65% + step-rate/promotional component, source YOS 1-25+. Build maps source YOS 1..24 → canonical YOS 0..23, source "25 & up" 2.95% → canonical YOS 24..70 flat. Spot-checked: yos 0=0.0895 (AV YOS 1 Total 8.95%), yos 1=0.0545 (AV YOS 2 Total 5.45%), yos 70=0.0295 (AV "25 & up" Total 2.95%). All match. |

### Decrements

| item | required | status | source_type | source citation | notes |
| --- | --- | --- | --- | --- | --- |
| retirement_rates | required | partial | AV-derived | AV_2024; printed p. 62 / PDF p. 69; Appendix 2 §2.d Rates of Retirement | Verified 2026-05-01: Normal retirement rates published M/F separately for ages 50-64; runtime accepts a single schedule so build uses arithmetic average — e.g., age 50 = (0.110+0.106)/2 = 0.108; age 60 = (0.150+0.178)/2 = 0.164; age 75+ = (1.000+1.000)/2 = 1.000. AV bands 65-69, 70-74, 75+ are expanded to single ages and carried flat through max_age=120. Early retirement rates are M/F-identical in source (45-59 = 0.006; 60-64 = 0.010-0.050); transcribed exactly. Status partial: M/F averaging is a known runtime-architecture simplification (one schedule). |
| reduction_gft | conditional | have | AV-direct | AV_2024; printed p. 47 / PDF p. 54; Appendix 1 grandfathered early-retirement reduction table | Verified 2026-05-01: spot-checked 6 ages × 11 yos against AV table. All values match (e.g., age 55/yos 20=0.90, age 60/yos 20=1.00, age 55/yos 25=1.00). 66 rows = 6 ages × 11 yos including "30 or more" mapped to canonical yos=30. |
| reduction_others | conditional | have | AV-direct | AV_2024; printed p. 47 / PDF p. 54; Appendix 1 non-grandfathered early-retirement reduction table | Verified 2026-05-01: all 11 values (ages 55-65 = 0.43, 0.46, 0.50, 0.55, 0.59, 0.64, 0.70, 0.76, 0.84, 0.91, 1.00) match the AV's single-row reduction table exactly. |
| termination_rates | required | have | AV-derived | AV_2024; printed p. 61 / PDF p. 68; Appendix 2 §2.b Rates of Termination | Verified 2026-05-01: select-and-ultimate structure preserved. Service-years table (AV YOS 1-10) → canonical YOS 0-9 (offset by 1); years_from_NR table (AV 1-32) → canonical years_from_nr 1-32 with explicit row 0 = 0.0 added by build. Spot-checked: yos 0=0.143011 (AV YOS 1), yos 9=0.041029 (AV YOS 10), years_from_nr 1=0.01691, years_from_nr 13=0.024966 — all match. |

### Mortality

| item | required | status | source_type | source citation | notes |
| --- | --- | --- | --- | --- | --- |
| base_rates | required | partial | estimated | AV_2024; SOA_PUB2010_AMOUNT; TXTRS_AV_PROTO; printed p. 60;64 / PDF p. 67;71; AV mortality narrative (active p. 60 / PDF 67; retiree p. 64 / PDF 71) + PubT-2010(B) Below-Median + TX prototype | Inspected 2026-05-01: 412 rows = 103 ages (18-120) × 2 genders × 2 member_types (employee, retiree). Active (employee) qx values are clean round numbers consistent with PubT-2010(B) Teacher Below-Median Income source-direct (e.g., male 50 = 0.00149, female 50 = 0.00093). Retiree qx values are spline-fitted estimator output (e.g., male 50 = 0.00207, female 50 = 0.00127). Status partial per issues #72 (AV-named 2021 TRS Healthy Pensioner table not public; fallback estimator used) and #73 (active improvement scale choice). |
| improvement_scale | required | have | AV-referenced-external | AV_2024; SOA_MP2021; printed p. 64 / PDF p. 71; Scale UMP 2021 (ultimate rates of MP-2021) | Verified 2026-05-01: 17574 rows = 101 ages (20-120) × 87 years (1951-2037) × 2 genders. Spot-checked 6 ages × 2 genders against prep/common/sources/soa_mp2021_rates.xlsx 2037+ ultimate column. All match exactly: age 20 = 0.0135, age 50 = 0.0135, age 80 = 0.011, age 100 = 0.003, age 120 = 0.0 (M and F identical because UMP-2021 ultimate rates are unisex by age). Confirmed immediate convergence: ultimate rate replicated flat across all 87 years for each age/gender. Immediate-convergence interpretation inferred from AV plus experience study plus GASB 67. |
| male_mp_forward_shift | optional | have | AV-direct | AV_2024; printed p. 60 / PDF p. 67; AV mortality assumptions narrative | 2 years forward per AV |
| mortality_base_table_name | required | have | runtime-only | — | Label "txtrs_av_av_first" identifies the AV-first build path |
| mortality_improvement_scale_name | required | have | runtime-only | — | Label "ump_2021_immediate" |

### Funding data

| item | required | status | source_type | source citation | notes |
| --- | --- | --- | --- | --- | --- |
| current_term_vested_cashflow | required | have | computed | — | Verified 2026-05-01: 37 rows = D + L = 12 + 25 with first 12 zero-payment (deferral) and last 25 equal $3,441,018,505 (payout, COLA=0 flat). Verifier scripts/build/verify_term_vested_cashflow.py confirms NPV identity holds at rel err 8.57e-16. Built from pvfb_term_current plus dr_current plus COLA plus term_vested D/L. Issue #76 tracked the build; D/L provenance refined in step 2 of audit. |
| return_scenarios | required | have | runtime-only | AV_2024; Table 12c HISTORY OF INVESTMENT RETURNS | Verified 2026-05-01: 100 years (2023-2122). Long-term return rate 7.00% in model and assumption columns matches AV Table 12c assumed return for FY 2023 and FY 2024 (already verified in scalar audit via Appendix 2 §1). Stress scenarios (recession, recur_recession, constant_6) are modeling-choice paths legacy-style: -24% shock + 11%/yr recovery + 6% steady; recur adds second shock at 2039. model and assumption columns are overridden at runtime by economic.model_return / dr_current. |
| amort_layers | conditional | N/A | — | — | No FRS-style layered amortization for txtrs-av |

### Modeling switches

| item | required | status | source_type | source citation | notes |
| --- | --- | --- | --- | --- | --- |
| entrant_salary_at_start_year | optional | have | runtime-only | — |  |
| use_earliest_retire | optional | N/A | runtime-only | — | Not present in txtrs-av config |

## What this checklist is for

- A single place to see, per plan, what is sourced, partially sourced, estimated, computed, or still missing.
- A reusable shape: copy `prep/common/input_checklist_template.csv` for a new plan, fill in the right-hand columns as documents arrive.
- Complementary to `artifact_provenance.csv`, `source_registry.csv`, and the artifact coverage matrix. The checklist drills into individual scalars in `init_funding.csv`, `valuation_inputs`, and the calibration block — places where one row per file is too coarse to see the gaps.
