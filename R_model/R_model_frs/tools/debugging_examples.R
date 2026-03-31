
source(here::here("tools", "libraries.R")) # load all tools
source(here::here("tools", "functions.R"))

source(here::here("testing", "libraries.R"))

checkUsage(add_new_entrants)

# codetools::findGlobals()
findGlobals(add_new_entrants, merge = TRUE)

findGlobals(add_new_entrants, merge = FALSE)
findGlobals(annfactor, merge = FALSE)
findGlobals(clean_mp_table, merge = FALSE)
findGlobals(clean_retire_rate_table, merge = FALSE)
findGlobals(cumFV2, merge = FALSE)
findGlobals(get_base_mort_table, merge = FALSE)
findGlobals(get_benefit_data, merge = FALSE) # 65 possible variables
findGlobals(get_early_retire_rate_table, merge = FALSE)
findGlobals(get_funding_data, merge = FALSE) # 32 variables
findGlobals(get_funding_table, merge = FALSE) # 4 variables
findGlobals(get_liability_data, merge = FALSE) # 98 variables
findGlobals(get_normal_retire_rate_table, merge = FALSE) # age
findGlobals(get_salary_headcount_table, merge = FALSE) # 13 vars
findGlobals(get_sep_type, merge = FALSE)
findGlobals(get_separation_table, merge = FALSE)
findGlobals(get_tier, merge = FALSE)
findGlobals(get_wf_data, merge = FALSE)

checkUsage(get_benefit_data)


# flow_run(make_sum(a=2, b=3))
flow_run(get_benefit_data(class_name = "regular"), browse = TRUE)