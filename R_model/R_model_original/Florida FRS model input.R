##################################################################
##                  Model Inputs & Assumptions                  ##
##################################################################

#1. Actuarial and economic assumptions:
dr_old_ <- 0.068             #previous year's discount rate
dr_current_ <- 0.067        #discount rate for current members
dr_new_ <- 0.067            #discount rate for new members
payroll_growth_ <- 0.0325   #payroll growth assumption
pop_growth_ <- 0            #plan's active population growth assumption
inflation_ <- 0.024         #inflation assumption

#2. Benefit assumptions:
db_ee_interest_rate_ <- 0

#Cost of living adjustment (COLA) assumptions:
cola_tier_1_active_constant_ <- "no" #If yes, COLA for tier 1 active members is constant instead of reduced
cola_tier_1_active_ <- 0.03 #COLA for tier 1 active members
cola_tier_2_active_ <- 0 #COLA for tier 2 active members
cola_tier_3_active_ <- 0 #COLA for tier 3 active members

cola_current_retire_ <- cola_tier_1_active_ #COLA for current retirees
cola_current_retire_one_ <- 0 #One-time COLA for current retirees
one_time_cola_ <- F   #One-time COLA or not? True means yes, False means no

#DC Employer contributions:
regular_er_dc_cont_rate_ <- 0.066            #Regular's employer DC contribution rate
special_er_dc_cont_rate_ <- 0.1654           #Special Risk's employer DC contribution rate
admin_er_dc_cont_rate_ <- 0.0843             #Special Risk Admin's employer DC contribution rate
judges_er_dc_cont_rate_ <- 0.1405            #Judges' employer DC contribution rate
eso_er_dc_cont_rate_ <- 0.1195               #Local's employer DC contribution rate
eco_er_dc_cont_rate_ <- 0.0994               #Leg-Atty-Cab's employer DC contribution rate
senior_management_er_dc_cont_rate_ <- 0.0798 #Senior Management's employer DC contribution rate

#3. Funding assumptions
# the plan simply adopts all recommendations from its actuary board, so the "statutory" policy is equivalent to the "ADC" policy. 
funding_policy_ <- "statutory"              #Plan's funding policy: "statutory" means a fixed contribution rate; "ADC" means an actuarially determined contribution rate. For FRS, this input is irrelevant since the plan's statutory policy is equivalent to its ADC policy. 
db_ee_cont_rate_ <- 0.03                    #DB employee contribution rate

#Amortization policy
amo_pay_growth_ <- payroll_growth_         #payroll growth assumption for amortization purposes
amo_period_new_ <- 20                       #amortization period for new unfunded liabilities
amo_method_ <- "level %"                    #amortization method: "level %" means level percentage of payroll amortization; "level $" means level dollar amortization

#Other policies:
funding_lag_ <- 1                            #This is the additional time (in years) that it takes for the determined contribution rate to take effect after 1 year. By the default, the contribution rate will take effect one year after it's determined (funding lag = 0).
                                             #If the funding lag is 1, then the contribution rate will take effect 2 years after it's determined. 

#4. Investment assumptions
return_scen_ <- "assumption"                 #The deterministic return scenario to be used in the funding model. 
model_return_ <- dr_new_                     #The return used under the "model" scenario. By default, this is the same as the discount rate for the new tier.
return_2023_ <- 0.067                        #The return for fiscal year 2023. This will be updated/removed when the 2023 val report comes out.

#5. Plan design assumptions
#FRS plan membership classes are: Regular, Special Risk, Special Risk Administrative, Judicial,  Legislators/Attorney/Cabinet (ECO), Local (ESO), Senior Management
class_name_ <- "regular"

#DB ratios below are the proportions of members who choose the DB plan. The remaining members choose the DC plan (Investment Plan)
special_db_legacy_before_2018_ratio_ <- 0.95      #for special-risk plan's members hired before 2018
non_special_db_legacy_before_2018_ratio_ <- 0.75  #for non-special risk plan's members hired before 2018
special_db_legacy_after_2018_ratio_ <- 0.85       #for special risk plan's members hired between 2018 and new_year
non_special_db_legacy_after_2018_ratio_ <- 0.25   #for non-special risk plan's members hired between 2018 and new_year
special_db_new_ratio_ <- 0.75                     #for special risk plan's members hired after new_year
non_special_db_new_ratio_ <- 0.25                 #for non-special risk plan's members hired after new_year


#6. Model assumptions 
model_period_ <- 30     #Projection period (typically 30 years)
min_age_ <- 18          #Age of the typical youngest member
max_age_ <- 120         #Max age from mortality assumptions
start_year_ <- 2022     #Year of the latest val report (update this when a new val report comes out)
new_year_ <- 2024       #Year for new entrants with a new tier to join (update this when a new val report comes out)
min_year_ <- 1970       #No hard rule about this. Should get back to about 40 years from now.   
max_year_ <- start_year_ + model_period_ + max_age_ - min_age_

entry_year_range_ <- min_year_:(start_year_ + model_period_)
# RetYear <- MinYear:(YearStart + ModelPeriod)
year_range_ <- min_year_:max_year_
age_range_ <- min_age_:max_age_
yos_range_ <- 0:70
# RetirementAge <- Age


#7. Retirement benefit assumptions
pension_payment_ <- 11944986866         #Pension Payments in Reconciliation of Market Value of Assets Used for Valuation table
contribution_refunds_ <- 28343757       #Contribution Refunds in Reconciliation of Market Value of Assets Used for Valuation table
disbursement_to_ip_ <- 768106850        #Disbursements to Investment Plan in Reconciliation of Market Value of Assets Used for Valuation table
admin_expense_ <- 22494571              #Administrative Expenses in Reconciliation of Market Value of Assets Used for Valuation table

ben_payment_ratio_ <- pension_payment_/(pension_payment_ + contribution_refunds_ + disbursement_to_ip_ + admin_expense_)

#Below are the cash outflows for each membership class. These numbers are Benefit Payments and other Disbursements in the Development of Actuarial Value of Assets table
regular_outflow_ <- 8967096000
special_outflow_ <- 2423470000
admin_outflow_ <- 8090000
judges_outflow_ <- 105844000
eso_outflow_ <- 53526000
eco_outflow_ <- 9442000
senior_management_outflow_ <- 338664000

#Below are the estimated benefit payments for each membership class
regular_ben_payment_current_ <- regular_outflow_ * ben_payment_ratio_
special_ben_payment_current_ <- special_outflow_ * ben_payment_ratio_
admin_ben_payment_current_ <- admin_outflow_ * ben_payment_ratio_
judges_ben_payment_current_ <- judges_outflow_ * ben_payment_ratio_
eso_ben_payment_current_ <- eso_outflow_ * ben_payment_ratio_
eco_ben_payment_current_ <- eco_outflow_ * ben_payment_ratio_
senior_management_ben_payment_current_ <- senior_management_outflow_ * ben_payment_ratio_

#Below are the numbers of annuitants for each membership class, representing the retiree populations
regular_retiree_pop_current_ <- 393308
special_retiree_pop_current_ <- 41696
admin_retiree_pop_current_ <- 160
judges_retiree_pop_current_ <- 989
eso_retiree_pop_current_ <- 1446
eco_retiree_pop_current_ <- 227
senior_management_retiree_pop_current_ <- 5828

#retire_refund_ratio is the ratio of vested members who choose to retire instead of getting a refund (i.e. a ratio of 0.8 means 80% of vested members choose to retire)
retire_refund_ratio_ <- 1

#Model Calibration
cal_factor_ <- 0.9                   #Calibration factor for the benefit model. This is to adjust the normal cost to match the normal cost from the val report.
                                     #Adjust this calibration factor after getting preliminary results from the benefit model.

regular_val_norm_cost_ <- 0.0896               #Normal cost for Regular members from the val report  
special_val_norm_cost_ <- 0.2013               #Normal cost for Special Risk members from the val report
admin_val_norm_cost_ <- 0.1457                 #Normal cost for Special Risk Admin members from the val report
judges_val_norm_cost_ <- 0.1777                #Normal cost for Judicial members from the val report
eso_val_norm_cost_ <- 0.1463                   #Normal cost for Local members from the val report
eco_val_norm_cost_ <- 0.1254                   #Normal cost for Leg-Atty-Cab members from the val report
senior_management_val_norm_cost_ <- 0.1086     #Normal cost for Senior Management members from the val report

#Below are calibration factors to further adjust the normal costs to match the numbers from the val report.These are calculated by dividing the normal costs from the val report by the normal costs from the benefit model.
regular_nc_cal_ <- regular_val_norm_cost_ / 0.09096784
special_nc_cal_ <- special_val_norm_cost_ / 0.2044051
admin_nc_cal_ <- admin_val_norm_cost_ / 0.10436284
judges_nc_cal_ <- judges_val_norm_cost_ / 0.1937982
eso_nc_cal_ <- eso_val_norm_cost_ / 0.1557111
eco_nc_cal_ <- eco_val_norm_cost_ / 0.1513904
senior_management_nc_cal_ <- senior_management_val_norm_cost_ / 0.11295223


#Assumptions about the "remaining" accrued liability (which is not accounted for by the PVFB calculations). 
#This is lumped together with the accrued liability for current term vested members.
#The value is calculated by subtracting the preliminary actuarial accrued liability produced by the liability model from the accrued liability from the val report.
#The preliminary accrued liability is the liability calculated by the liability model when these values below are set to 0.
regular_pvfb_term_current_ <- 145585523000 - 138993598036
special_pvfb_term_current_ <- 45070773000 - 41833009006
admin_pvfb_term_current_ <- 90337000 - 92432291
eco_pvfb_term_current_ <- 138008000 - 110403603
eso_pvfb_term_current_ <- 751363000 - 720397602
judges_pvfb_term_current_ <- 1545348000 - 1444240024
senior_management_pvfb_term_current_ <- 6039701000 - 5404229360

amo_period_term_ <- 50        #Amortization period for the remaining accrued liability
amo_term_growth_ <- 0.03      #Growth rate of the annual amortization payments for the remaining accrued liability
#Note: we've switched to a new amortization method for the remaining accrued liability that produces amo payments fitting a bell curve instead of growing at a constant rate. This new method has not yet been implemented for Florida FRS but will be in the next update.

#Membership assumptions
#Below are the total membership numbers for each membership class. These numbers are from the ACFR and include both DB and DC membership. 
regular_total_active_member_ <- 537128
special_total_active_member_ <- 72925
admin_total_active_member_ <- 104
eco_eso_judges_total_active_member_ <- 2075
senior_management_total_active_member_ <- 7610



#7. Import key data tables
FileName <- 'Florida FRS inputs.xlsx'

base_teacher_mort_table_ <- read_excel("pub-2010-headcount-mort-rates.xlsx", sheet = "PubT.H-2010")
base_safety_mort_table_ <- read_excel("pub-2010-headcount-mort-rates.xlsx", sheet = "PubS.H-2010")
base_general_mort_table_ <- read_excel("pub-2010-headcount-mort-rates.xlsx", sheet = "PubG.H-2010")

male_mp_table_ <- read_excel("mortality-improvement-scale-mp-2018-rates.xlsx", sheet = "Male")
female_mp_table_ <- read_excel("mortality-improvement-scale-mp-2018-rates.xlsx", sheet = "Female")

salary_growth_table_ <- read_excel(FileName, sheet = "Salary Growth")

regular_salary_table_ <- read_excel(FileName, sheet="Salary Distribution Regular")
regular_headcount_table_ <- read_excel(FileName, sheet="HeadCount Distribution Regular") %>% 
  mutate(across(everything(), ~replace(.x, is.na(.x), 0)))

special_salary_table_ <- read_excel(FileName, sheet="Salary Distribution Special")
special_headcount_table_ <- read_excel(FileName, sheet="HeadCount Distribution Special") %>% 
  mutate(across(everything(), ~replace(.x, is.na(.x), 0)))

admin_salary_table_ <- read_excel(FileName, sheet="Salary Distribution Admin")
admin_headcount_table_ <- read_excel(FileName, sheet="HeadCount Distribution Admin") %>% 
  mutate(across(everything(), ~replace(.x, is.na(.x), 0)))

eco_salary_table_ <- read_excel(FileName, sheet="Salary Distribution Eco")
eco_headcount_table_ <- read_excel(FileName, sheet="HeadCount Distribution Eco") %>% 
  mutate(across(everything(), ~replace(.x, is.na(.x), 0)))

eso_salary_table_ <- read_excel(FileName, sheet="Salary Distribution Eso")
eso_headcount_table_ <- read_excel(FileName, sheet="HeadCount Distribution Eso") %>% 
  mutate(across(everything(), ~replace(.x, is.na(.x), 0)))

judges_salary_table_ <- read_excel(FileName, sheet="Salary Distribution Judge")
judges_headcount_table_ <- read_excel(FileName, sheet="HeadCount Distribution Judge") %>% 
  mutate(across(everything(), ~replace(.x, is.na(.x), 0)))

senior_management_salary_table_ <- read_excel(FileName, sheet="Salary Distribution Sen Man")
senior_management_headcount_table_ <- read_excel(FileName, sheet="HeadCount Distribution Sen Man") %>% 
  mutate(across(everything(), ~replace(.x, is.na(.x), 0)))

# Retirement rate tables

drop_entry_tier_1_table_ <- read_excel("Reports/extracted inputs/drop entry tier 1.xlsx")
drop_entry_tier_2_table_ <- read_excel("Reports/extracted inputs/drop entry tier 2.xlsx")

normal_retirement_tier_1_table_ <- read_excel("Reports/extracted inputs/normal retirement tier 1.xlsx")
normal_retirement_tier_2_table_ <- read_excel("Reports/extracted inputs/normal retirement tier 2.xlsx")

early_retirement_tier_1_table_ <- read_excel("Reports/extracted inputs/early retirement tier 1.xlsx")
early_retirement_tier_2_table_ <- read_excel("Reports/extracted inputs/early retirement tier 2.xlsx")

#Termination rate tables

regular_term_rate_male_table_ <- read_excel(FileName, sheet = "Withdrawal Rate Regular Male")
regular_term_rate_female_table_ <- read_excel(FileName, sheet = "Withdrawal Rate Regular Female")

special_term_rate_male_table_ <- read_excel(FileName, sheet = "Withdrawal Rate Special Male")
special_term_rate_female_table_ <- read_excel(FileName, sheet = "Withdrawal Rate Special Female")

admin_term_rate_male_table_ <- read_excel(FileName, sheet = "Withdrawal Rate Admin Male")
admin_term_rate_female_table_ <- read_excel(FileName, sheet = "Withdrawal Rate Admin Female")

eco_term_rate_male_table_ <- read_excel(FileName, sheet = "Withdrawal Rate Eco")
eco_term_rate_female_table_ <- read_excel(FileName, sheet = "Withdrawal Rate Eco")

eso_term_rate_male_table_ <- read_excel(FileName, sheet = "Withdrawal Rate Eso")
eso_term_rate_female_table_ <- read_excel(FileName, sheet = "Withdrawal Rate Eso")

judges_term_rate_male_table_ <- read_excel(FileName, sheet = "Withdrawal Rate Judges")
judges_term_rate_female_table_ <- read_excel(FileName, sheet = "Withdrawal Rate Judges")

senior_management_term_rate_male_table_ <- read_excel(FileName, sheet = "Withdrawal Rate Sen Man Male")
senior_management_term_rate_female_table_ <- read_excel(FileName, sheet = "Withdrawal Rate Sen Man Female")


retiree_distribution <- read_excel(FileName, sheet = "Retiree Distribution") 

init_funding_data <- read_excel(FileName, sheet = "Funding Input")
return_scenarios <- read_excel(FileName, sheet = "Return Scenarios")

current_amort_layers_table_ <- read_excel(FileName, sheet = "Amort Input")
