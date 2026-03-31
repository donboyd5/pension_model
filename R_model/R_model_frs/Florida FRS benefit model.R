#################################################################
##                Salary & Headcount Processing                ##
#################################################################

#Calculate salary cumulative growth 
salary_growth_table <- salary_growth_table_ %>% 
  bind_rows(tibble(yos = (max(salary_growth_table_$yos)+1):max(yos_range_))) %>% 
  fill(everything(), .direction = "down") %>% 
  mutate(across(contains("salary"), ~ cumprod(1 + lag(.x, default = 0)), .names = "cumprod_{.col}"), .keep = "unused")


#Joining headcount data, salary data, and salary growth data
#We account for the Investment Plan (DC plan) head count by inflating the DB head count by the ratio of total system head count to DB head count
#ECO, ESO, and Judges head counts are processed separately as the ACFR does not provide detailed head counts for these classes 
eco_eso_judges_active_member_adjustment_ratio <- eco_eso_judges_total_active_member_ / sum(eco_headcount_table_[-1] + eso_headcount_table_[-1] + judges_headcount_table_[-1])

get_salary_headcount_table <- function(salary_table, headcount_table, salary_growth_table, class_name){
  
  class_name <- str_replace(class_name, " ", "_")
  
  if (!class_name %in% c("eco", "eso", "judges")) {
    assign("total_active_member", get(paste0(class_name, "_total_active_member_")))
  } else {
    assign("total_active_member", get("eco_eso_judges_total_active_member_"))
  }
  
  salary_growth_table <- salary_growth_table %>% 
    select(yos, contains(class_name)) %>% 
    rename(cumprod_salary_increase = 2)
  
  salary_table_long <- salary_table %>% 
    pivot_longer(cols = -1, names_to = "yos", values_to = "salary")
  
  headcount_table_long <- headcount_table %>% 
    pivot_longer(cols = -1, names_to = "yos", values_to = "count") %>% 
    mutate(
      active_member_adjustment_ratio = if_else(str_detect(class_name, "eco|eso|judges"), eco_eso_judges_active_member_adjustment_ratio, 
                                               total_active_member / sum(count, na.rm = T)),
      count = count * active_member_adjustment_ratio
    ) %>% 
    select(-active_member_adjustment_ratio)
  
  salary_headcount_table <- salary_table_long %>% 
    left_join(headcount_table_long) %>% 
    mutate(
      yos = as.numeric(yos),
      start_year = start_year_,
      entry_age = age - yos,
      entry_year = start_year - yos) %>% 
    filter(!is.na(salary), entry_age >= 18) %>% 
    left_join(salary_growth_table) %>% 
    mutate(entry_salary = salary / cumprod_salary_increase) %>% 
    select(entry_year, entry_age, age, yos, count, entry_salary)
  
  entrant_profile <- salary_headcount_table %>% 
    filter(entry_year == max(entry_year)) %>% 
    mutate(entrant_dist = count/sum(count)) %>% 
    select(entry_age, entry_salary, entrant_dist) %>% 
    rename(start_sal = entry_salary)
  
  output <- list(
    salary_headcount_table = salary_headcount_table, 
    entrant_profile = entrant_profile)
    
  return(output)
}

regular_salary_headcount_table <- get_salary_headcount_table(regular_salary_table_, regular_headcount_table_, salary_growth_table, "regular")$salary_headcount_table
regular_entrant_profile_table <- get_salary_headcount_table(regular_salary_table_, regular_headcount_table_, salary_growth_table, "regular")$entrant_profile

special_salary_headcount_table <- get_salary_headcount_table(special_salary_table_, special_headcount_table_, salary_growth_table, "special")$salary_headcount_table
special_entrant_profile_table <- get_salary_headcount_table(special_salary_table_, special_headcount_table_, salary_growth_table, "special")$entrant_profile

admin_salary_headcount_table <- get_salary_headcount_table(admin_salary_table_, admin_headcount_table_, salary_growth_table, "admin")$salary_headcount_table
admin_entrant_profile_table <- get_salary_headcount_table(admin_salary_table_, admin_headcount_table_, salary_growth_table, "admin")$entrant_profile

eco_salary_headcount_table <- get_salary_headcount_table(eco_salary_table_, eco_headcount_table_, salary_growth_table, "eco")$salary_headcount_table
eco_entrant_profile_table <- get_salary_headcount_table(eco_salary_table_, eco_headcount_table_, salary_growth_table, "eco")$entrant_profile

eso_salary_headcount_table <- get_salary_headcount_table(eso_salary_table_, eso_headcount_table_, salary_growth_table, "eso")$salary_headcount_table
eso_entrant_profile_table <- get_salary_headcount_table(eso_salary_table_, eso_headcount_table_, salary_growth_table, "eso")$entrant_profile

judges_salary_headcount_table <- get_salary_headcount_table(judges_salary_table_, judges_headcount_table_, salary_growth_table, "judges")$salary_headcount_table
judges_entrant_profile_table <- get_salary_headcount_table(judges_salary_table_, judges_headcount_table_, salary_growth_table, "judges")$entrant_profile

senior_management_salary_headcount_table <- get_salary_headcount_table(senior_management_salary_table_, 
                                            senior_management_headcount_table_, salary_growth_table, "senior management")$salary_headcount_table
senior_management_entrant_profile_table <- get_salary_headcount_table(senior_management_salary_table_, 
                                            senior_management_headcount_table_, salary_growth_table, "senior management")$entrant_profile


##################################################################
##              Retirement & Separation Conditions              ##
##################################################################
#Current two tiers:
## Members joining before July 1, 2011 (tier 1)
## Members joining after July 1, 2011 (tier 2)

#tier 3: for new hires joining as of new_year_

get_tier <- function(class_name, entry_year, age, yos){
  tier = if_else(entry_year < 2011,
                     case_when(
                       class_name %in% c("special", "admin") & (yos >= 25 | (age >= 55 & yos >= 6) | (age >= 52 & yos >= 25)) ~ "tier_1_norm",
                       yos >= 30 | (age >= 62 & yos >= 6) ~ "tier_1_norm",
                       class_name %in% c("special", "admin") & (yos >= 6 & age >= 53) ~ "tier_1_early",
                       (yos >= 6 & age >= 58) ~ "tier_1_early",
                       yos >= 6 ~ "tier_1_vested",
                       .default = "tier_1_non_vested"
                     ),
                     if_else(entry_year < new_year_,
                             case_when(
                               class_name %in% c("special", "admin") & (yos >= 30 | (age >= 60 & yos >= 8)) ~ "tier_2_norm",
                               yos >= 33 | (age >= 65 & yos >= 8) ~ "tier_2_norm",
                               class_name %in% c("special", "admin") & (yos >= 8 & age >= 56) ~ "tier_2_early",
                               (yos >= 8 & age >= 61) ~ "tier_2_early",
                               yos >= 8 ~ "tier_2_vested",
                               .default = "tier_2_non_vested"
                             ),
                             case_when(
                               class_name %in% c("special", "admin") & (yos >= 30 | (age >= 60 & yos >= 8)) ~ "tier_3_norm",
                               yos >= 33 | (age >= 65 & yos >= 8) ~ "tier_3_norm",
                               class_name %in% c("special", "admin") & (yos >= 8 & age >= 56) ~ "tier_3_early",
                               (yos >= 8 & age >= 61) ~ "tier_3_early",
                               yos >= 8 ~ "tier_3_vested",
                               .default = "tier_3_non_vested"
                             )))
  return(tier)
}

#Separation type function
get_sep_type <- function(tier) {
  sep_type <- case_when(
    str_detect(tier, "early|norm|reduced") ~ "retire",
    str_detect(tier, "non_vested") ~ "non_vested",
    str_detect(tier, "vested") ~ "vested"
  )
}

#################################################################
##                    Mortality Assumptions                    ##
#################################################################
#Clean up mortality table
get_base_mort_table <- function(raw_mort_table){
  base_mort_table <- raw_mort_table %>% 
    #remove the first three rows and then remove empty columns
    slice(-(1:3)) %>% 
    remove_empty() %>% 
    #elevate first row to become col names, then clean col names
    row_to_names(row_number = 1) %>% 
    clean_names() %>% 
    select(-na) %>% 
    #rename columns to differentiate female and male rates
    rename_with(.fn = ~ paste0(.x, "_female"),
                .cols = !(ends_with("2") | contains("age"))) %>% 
    rename_with(.fn = ~ paste0(str_replace(.x, "2", ""), "male"),
                .cols = ends_with("2")) %>% 
    #turn data into numeric 
    mutate(across(everything(), ~ as.numeric(.x)),
           employee_female = if_else(is.na(employee_female), healthy_retiree_female, employee_female),
           employee_male = if_else(is.na(employee_male), healthy_retiree_male, employee_male),
           healthy_retiree_female = if_else(is.na(healthy_retiree_female), employee_female, healthy_retiree_female),
           healthy_retiree_male = if_else(is.na(healthy_retiree_male), employee_male, healthy_retiree_male))
  return(base_mort_table)
}

base_general_mort_table <- get_base_mort_table(base_general_mort_table_)
base_teacher_mort_table <- get_base_mort_table(base_teacher_mort_table_)
base_safety_mort_table <- get_base_mort_table(base_safety_mort_table_)

#Create this mort table for regular employees who are either teachers or general employees
base_regular_mort_table <- (base_general_mort_table + base_teacher_mort_table)/2

#Clean up mortality improvement (MP) tables
clean_mp_table <- function(raw_mp_table, extend_2_yrs = F){
  mp_table <- raw_mp_table %>%
    row_to_names(row_number = 1) %>% 
    rename(age = 1) %>%
    rename_with(.fn = ~ str_replace(.x, "\\+", ""),
                .col = ends_with("+")) %>% 
    mutate(age = replace(age, age == "≤ 20", 20)) %>% 
    mutate(across(everything(), ~ as.numeric(.x))) 
  
  if (extend_2_yrs == T){
    mp_table <- mp_table %>% 
      add_row(age=19, .before = 1) %>% 
      add_row(age=18, .before = 1) %>% 
      fill(everything(), .direction = "up")
  }

  return(mp_table)
}

male_mp_table <- clean_mp_table(male_mp_table_, extend_2_yrs = T)
female_mp_table <- clean_mp_table(female_mp_table_, extend_2_yrs = T)

#Modify mortality improvement rates
#base_year is the year when the base mort rate is given. It's 2010 in this case
get_mp_final_table <- function(mp_table, gender, base_year){
  mp_table <- mp_table %>% 
    pivot_longer(-age, names_to = "year", values_to = "mp") %>% 
    mutate(year = as.numeric(year))
  
  mp_ultimate_table <- mp_table %>%       #ultimate rates = rates for the last year in the MP table
    filter(year == max(year)) %>% 
    rename(mp_ultimate = mp) %>% 
    select(-year)
  
  mp_final_table <- expand_grid(age = age_range_, year = min(mp_table$year):max(year_range_)) %>% 
    left_join(mp_table) %>% 
    left_join(mp_ultimate_table, by = "age") %>% 
    mutate(mp_final = if_else(year > max(mp_table$year), mp_ultimate, mp)) %>% 
    group_by(age) %>% 
    
    mutate(mp_cumprod_raw = cumprod(1 - mp_final),
           #The adjusted value is the ratio of the raw value and the anchor point in base year
           mp_cumprod_adj = mp_cumprod_raw / mp_cumprod_raw[year == base_year]) %>%
    ungroup() %>% 
    rename_with(.fn = ~ paste0(gender, "_", .x),
                .col = contains("mp")) %>% 
    select(age, year, contains("adj"))
  
  return(mp_final_table)
}


male_mp_final_table <- get_mp_final_table(male_mp_table, "male", 2010)
female_mp_final_table <- get_mp_final_table(female_mp_table, "female", 2010)

##Mortality calculations
get_mort_table <- function(class_name, base_mort_table, male_mp_final_table, female_mp_final_table, entrant_profile){
  final_mort_table <- expand_grid(entry_year = entry_year_range_, entry_age = entrant_profile$entry_age, dist_age = age_range_, yos = yos_range_) %>% 
    mutate(
      term_year = entry_year + yos,
      dist_year = entry_year + dist_age - entry_age
      )  %>% 
    filter(term_year <= dist_year) %>% 
    arrange(entry_year, entry_age, yos, dist_age) %>% 
    left_join(base_mort_table, by = c("dist_age" = "age")) %>% 
    left_join(male_mp_final_table, by = c("dist_age" = "age", "dist_year" = "year")) %>% 
    left_join(female_mp_final_table, by = c("dist_age" = "age", "dist_year" = "year")) %>% 
    mutate(
      tier_at_dist_age = get_tier(class_name, entry_year, dist_age, yos),
      
      male_mort = if_else(str_detect(tier_at_dist_age, "vested"), employee_male,
                          healthy_retiree_male) * male_mp_cumprod_adj,
      
      female_mort = if_else(str_detect(tier_at_dist_age, "vested"), employee_female,
                            healthy_retiree_female) * female_mp_cumprod_adj,
      
      mort_final = (male_mort + female_mort)/2
      ) %>% 
    #filter out the necessary variables
    select(entry_year, entry_age, dist_year, dist_age, yos, term_year, mort_final, tier_at_dist_age)
}


regular_mort_table <- get_mort_table("regular", base_regular_mort_table, male_mp_final_table, female_mp_final_table, regular_entrant_profile_table)
special_mort_table <- get_mort_table("special", base_safety_mort_table, male_mp_final_table, female_mp_final_table, special_entrant_profile_table)
admin_mort_table <- get_mort_table("admin", base_safety_mort_table, male_mp_final_table, female_mp_final_table, admin_entrant_profile_table)
eco_mort_table <- get_mort_table("eco", base_general_mort_table, male_mp_final_table, female_mp_final_table, eco_entrant_profile_table)
eso_mort_table <- get_mort_table("eso", base_general_mort_table, male_mp_final_table, female_mp_final_table, eso_entrant_profile_table)
judges_mort_table <- get_mort_table("judges", base_general_mort_table, male_mp_final_table, female_mp_final_table, judges_entrant_profile_table)
senior_management_mort_table <- get_mort_table("senior management", base_general_mort_table, male_mp_final_table, female_mp_final_table, senior_management_entrant_profile_table)


#Create a second mortality table for current retirees
get_mort_retire_table <- function(base_mort_table, male_mp_final_table, female_mp_final_table){
  
  mort_retire_table <- expand_grid(age = age_range_[age_range_ >= 40], year = year_range_[year_range_ >= start_year_]) %>% 
    left_join(base_mort_table, by = "age") %>% 
    left_join(male_mp_final_table, by = c("age", "year")) %>% 
    left_join(female_mp_final_table, by = c("age", "year")) %>% 
    mutate(base_age = age - (year - start_year_),
           male_mort = healthy_retiree_male * male_mp_cumprod_adj,
           female_mort = healthy_retiree_female * female_mp_cumprod_adj,
           mort_final = (male_mort + female_mort)/2) %>% 
    select(base_age, age, year, mort_final) %>% 
    filter(base_age >= 40) %>%
    arrange(base_age)
  
  return(mort_retire_table)
}

regular_mort_retire_table <- get_mort_retire_table(base_regular_mort_table, male_mp_final_table, female_mp_final_table)
special_mort_retire_table <- get_mort_retire_table(base_safety_mort_table, male_mp_final_table, female_mp_final_table)
admin_mort_retire_table <- get_mort_retire_table(base_safety_mort_table, male_mp_final_table, female_mp_final_table)
eco_mort_retire_table <- get_mort_retire_table(base_general_mort_table, male_mp_final_table, female_mp_final_table)
eso_mort_retire_table <- get_mort_retire_table(base_general_mort_table, male_mp_final_table, female_mp_final_table)
judges_mort_retire_table <- get_mort_retire_table(base_general_mort_table, male_mp_final_table, female_mp_final_table)
senior_management_mort_retire_table <- get_mort_retire_table(base_general_mort_table, male_mp_final_table, female_mp_final_table)


##############################################################################################################################
##################################################################
##                    Separation Assumptions                    ##
##################################################################
# Clean up retirement rate tables

clean_retire_rate_table <- function(df, col_names){
  
  index_of_na_row_from_bottom <- tail(which(rowSums(is.na(df)) == ncol(df)),1)
  index_of_row_before_body <- which(df[,1] == "Age")
  
  df <- df %>% 
    slice(-(index_of_na_row_from_bottom:n())) %>% 
    slice(-(1:index_of_row_before_body)) %>% 
    select_if(~any(!is.na(.)))
  
  index_of_70_79_row <- which(df[,1] == "70-79")
  
  names(df) <- col_names
  
  df <- df %>% 
    add_row(age=as.character(71:79), .after=index_of_70_79_row) %>% 
    mutate(
      age = replace(age, age == "70-79", "70"),
      across(everything(), ~as.numeric(.x))
    ) %>% 
    fill(everything(), .direction = "down")
  
  return(df)
}

drop_entry_table_col_names <- c("age", "regular_inst_female", "regular_inst_male",
               "regular_non_inst_female", "regular_non_inst_male",
               "special_risk_non_leo_female", "special_risk_non_leo_male",
               "special_risk_leo_female", "special_risk_leo_male",
               "other_female", "other_male")

normal_retire_table_col_names <- c("age", "regular_inst_female", "regular_inst_male",
                             "regular_non_inst_female", "regular_non_inst_male",
                             "special_risk_female", "special_risk_male",
                             "eco_eso_jud_female", "eco_eso_jud_male",
                             "senior_management_female", "senior_management_male")

early_retire_table_col_names <- c("age", "regular_non_inst_female", "regular_non_inst_male",
                                  "special_risk_female", "special_risk_male",
                                  "eco_eso_jud_female", "eco_eso_jud_male",
                                  "senior_management_female", "senior_management_male")


drop_entry_tier_1_table <- clean_retire_rate_table(drop_entry_tier_1_table_, drop_entry_table_col_names)
drop_entry_tier_2_table <- clean_retire_rate_table(drop_entry_tier_2_table_, drop_entry_table_col_names)

normal_retire_rate_tier_1_table <- clean_retire_rate_table(normal_retirement_tier_1_table_, normal_retire_table_col_names)
normal_retire_rate_tier_2_table <- clean_retire_rate_table(normal_retirement_tier_2_table_, normal_retire_table_col_names)

early_retire_rate_tier_1_table <- clean_retire_rate_table(early_retirement_tier_1_table_, early_retire_table_col_names)
early_retire_rate_tier_2_table <- clean_retire_rate_table(early_retirement_tier_2_table_, early_retire_table_col_names)


normal_retire_rate_tier_2_table <- normal_retire_rate_tier_2_table %>% 
  add_row(age=45:49, .before=1) %>% 
  mutate(across(everything(), ~replace(.x, is.na(.x), 0)))
  # mutate_all(~replace(., is.na(.), 0))

special_risk_drop_entry_tier_1_table <- drop_entry_tier_1_table %>% 
  select(age, contains("special_risk")) %>% 
  mutate(
    special_risk_female = (special_risk_non_leo_female + special_risk_leo_female)/2,
    special_risk_male = (special_risk_non_leo_male + special_risk_leo_male)/2,
    .keep = "unused"
    )

special_risk_drop_entry_tier_2_table <- drop_entry_tier_2_table %>% 
  select(age, contains("special_risk")) %>% 
  mutate(
    special_risk_female = (special_risk_non_leo_female + special_risk_leo_female)/2,
    special_risk_male = (special_risk_non_leo_male + special_risk_leo_male)/2,
    .keep = "unused"
  )
  
get_normal_retire_rate_table <- function(class_name, drop_entry_table, normal_retire_rate_table){
  
  if (class_name %in% c("eco", "eso", "judge")) {
    search_text_in_drop_entry_table = "other"
    search_text_in_normal_retire_table = "eco_eso_jud"
  } else if (class_name == "senior management") {
    search_text_in_drop_entry_table = "other"
    search_text_in_normal_retire_table = "senior_management"
  } else if (class_name == "admin"){
    search_text_in_drop_entry_table = search_text_in_normal_retire_table = "special"
  } else {
    search_text_in_drop_entry_table = search_text_in_normal_retire_table = class_name
  }
  
  normal_retire_rate_table <- (drop_entry_table %>% select(contains(search_text_in_drop_entry_table)) + 
                                 normal_retire_rate_table %>% select(contains(search_text_in_normal_retire_table))) %>% 
    add_column(age = drop_entry_table$age, .before = 1) %>% 
    rowwise() %>% 
    mutate(normal_retire_rate = mean(c_across(-age)), .keep = "unused") %>% 
    ungroup()
  
  return(normal_retire_rate_table)
}

regular_normal_retire_rate_tier_1_table <- get_normal_retire_rate_table(class_name = "regular",
                                                                        drop_entry_table = drop_entry_tier_1_table,
                                                                        normal_retire_rate_table = normal_retire_rate_tier_1_table)

regular_normal_retire_rate_tier_2_table <- get_normal_retire_rate_table(class_name = "regular",
                                                                        drop_entry_table = drop_entry_tier_2_table,
                                                                        normal_retire_rate_table = normal_retire_rate_tier_2_table)

special_normal_retire_rate_tier_1_table <- get_normal_retire_rate_table(class_name = "special",
                                                                        drop_entry_table = special_risk_drop_entry_tier_1_table,
                                                                        normal_retire_rate_table = normal_retire_rate_tier_1_table)

special_normal_retire_rate_tier_2_table <- get_normal_retire_rate_table(class_name = "special",
                                                                        drop_entry_table = special_risk_drop_entry_tier_2_table,
                                                                        normal_retire_rate_table = normal_retire_rate_tier_2_table)

admin_normal_retire_rate_tier_1_table <- get_normal_retire_rate_table(class_name = "admin",
                                                                        drop_entry_table = special_risk_drop_entry_tier_1_table,
                                                                        normal_retire_rate_table = normal_retire_rate_tier_1_table)

admin_normal_retire_rate_tier_2_table <- get_normal_retire_rate_table(class_name = "admin",
                                                                        drop_entry_table = special_risk_drop_entry_tier_2_table,
                                                                        normal_retire_rate_table = normal_retire_rate_tier_2_table)

eco_normal_retire_rate_tier_1_table <- get_normal_retire_rate_table(class_name = "eco",
                                                                        drop_entry_table = drop_entry_tier_1_table,
                                                                        normal_retire_rate_table = normal_retire_rate_tier_1_table)

eco_normal_retire_rate_tier_2_table <- get_normal_retire_rate_table(class_name = "eco",
                                                                        drop_entry_table = drop_entry_tier_2_table,
                                                                        normal_retire_rate_table = normal_retire_rate_tier_2_table)

eso_normal_retire_rate_tier_1_table <- get_normal_retire_rate_table(class_name = "eso",
                                                                    drop_entry_table = drop_entry_tier_1_table,
                                                                    normal_retire_rate_table = normal_retire_rate_tier_1_table)

eso_normal_retire_rate_tier_2_table <- get_normal_retire_rate_table(class_name = "eso",
                                                                    drop_entry_table = drop_entry_tier_2_table,
                                                                    normal_retire_rate_table = normal_retire_rate_tier_2_table)

judges_normal_retire_rate_tier_1_table <- get_normal_retire_rate_table(class_name = "judge",
                                                                    drop_entry_table = drop_entry_tier_1_table,
                                                                    normal_retire_rate_table = normal_retire_rate_tier_1_table)

judges_normal_retire_rate_tier_2_table <- get_normal_retire_rate_table(class_name = "judge",
                                                                    drop_entry_table = drop_entry_tier_2_table,
                                                                    normal_retire_rate_table = normal_retire_rate_tier_2_table)

  
senior_management_normal_retire_rate_tier_1_table <- get_normal_retire_rate_table(class_name = "senior management",
                                                                       drop_entry_table = drop_entry_tier_1_table,
                                                                       normal_retire_rate_table = normal_retire_rate_tier_1_table)

senior_management_normal_retire_rate_tier_2_table <- get_normal_retire_rate_table(class_name = "senior management",
                                                                       drop_entry_table = drop_entry_tier_2_table,
                                                                       normal_retire_rate_table = normal_retire_rate_tier_2_table)

  
get_early_retire_rate_table <- function(class_name, init_early_retire_rate_table){
  if (class_name %in% c("eco", "eso", "judge")) {
    search_text = "eco_eso_jud"
  } else if (class_name == "senior management") {
    search_text = "senior_management"
  } else if (class_name == "admin"){
    search_text = "special"
  } else {
    search_text = class_name
  }
  
  final_early_retire_rate_table <- init_early_retire_rate_table %>% 
    select(age, contains(search_text)) %>% 
    rowwise() %>% 
    mutate(early_retire_rate = mean(c_across(-age)), .keep = "unused") %>% 
    ungroup()
  
  return(final_early_retire_rate_table)
}

regular_early_retire_rate_tier_1_table <- get_early_retire_rate_table(class_name = "regular",
                                                               init_early_retire_rate_table = early_retire_rate_tier_1_table)

regular_early_retire_rate_tier_2_table <- get_early_retire_rate_table(class_name = "regular",
                                                                      init_early_retire_rate_table = early_retire_rate_tier_2_table)


special_early_retire_rate_tier_1_table <- get_early_retire_rate_table(class_name = "special",
                                                                      init_early_retire_rate_table = early_retire_rate_tier_1_table)

special_early_retire_rate_tier_2_table <- get_early_retire_rate_table(class_name = "special",
                                                                      init_early_retire_rate_table = early_retire_rate_tier_2_table)


admin_early_retire_rate_tier_1_table <- get_early_retire_rate_table(class_name = "admin",
                                                                      init_early_retire_rate_table = early_retire_rate_tier_1_table)

admin_early_retire_rate_tier_2_table <- get_early_retire_rate_table(class_name = "admin",
                                                                      init_early_retire_rate_table = early_retire_rate_tier_2_table)

eco_early_retire_rate_tier_1_table <- get_early_retire_rate_table(class_name = "eco",
                                                                      init_early_retire_rate_table = early_retire_rate_tier_1_table)

eco_early_retire_rate_tier_2_table <- get_early_retire_rate_table(class_name = "eco",
                                                                  init_early_retire_rate_table = early_retire_rate_tier_2_table)

eso_early_retire_rate_tier_1_table <- get_early_retire_rate_table(class_name = "eso",
                                                                  init_early_retire_rate_table = early_retire_rate_tier_1_table)

eso_early_retire_rate_tier_2_table <- get_early_retire_rate_table(class_name = "eso",
                                                                      init_early_retire_rate_table = early_retire_rate_tier_2_table)

judges_early_retire_rate_tier_1_table <- get_early_retire_rate_table(class_name = "judge",
                                                                  init_early_retire_rate_table = early_retire_rate_tier_1_table)

judges_early_retire_rate_tier_2_table <- get_early_retire_rate_table(class_name = "judge",
                                                                  init_early_retire_rate_table = early_retire_rate_tier_2_table)


senior_management_early_retire_rate_tier_1_table <- get_early_retire_rate_table(class_name = "senior management",
                                                                     init_early_retire_rate_table = early_retire_rate_tier_1_table)

senior_management_early_retire_rate_tier_2_table <- get_early_retire_rate_table(class_name = "senior management",
                                                                     init_early_retire_rate_table = early_retire_rate_tier_2_table)


get_separation_table <- function(class_name){
  
  # class_name <- gsub(" ", "_", class_name)
  class_name <- str_replace(class_name, " ", "_")
  
  assign("term_rate_male_table", get(paste0(class_name, "_term_rate_male_table_")))
  assign("term_rate_female_table", get(paste0(class_name, "_term_rate_female_table_")))
  
  assign("normal_retire_rate_tier_1_table", get(paste0(class_name, "_normal_retire_rate_tier_1_table")))
  assign("normal_retire_rate_tier_2_table", get(paste0(class_name, "_normal_retire_rate_tier_2_table")))
  
  assign("early_retire_rate_tier_1_table", get(paste0(class_name, "_early_retire_rate_tier_1_table")))
  assign("early_retire_rate_tier_2_table", get(paste0(class_name, "_early_retire_rate_tier_2_table")))
  
  assign("entrant_profile_table", get(paste0(class_name, "_entrant_profile_table")))
  
  term_rate_table <- ((term_rate_male_table + term_rate_female_table) / 2) %>% 
    add_row(yos = (max(term_rate_male_table$yos) + 1):max(yos_range_)) %>% 
    fill(everything(), .direction="down")
  
  breaks <- c(-Inf, 24, 29, 34, 44, 54, Inf)
  labels <- names(term_rate_table)[-1]
  
  long_term_rate_table <- pivot_longer(term_rate_table, cols = -yos, names_to = "age_group", values_to = "term_rate")
  
  sep_rate_table <- expand_grid(entry_year = entry_year_range_, term_age = age_range_, yos = yos_range_) %>% 
    mutate(
      entry_age = term_age  - yos,
      term_year = entry_year + yos,
      age_group = cut(term_age, breaks, labels)
      ) %>% 
    filter(entry_age %in% entrant_profile_table$entry_age) %>% 
    arrange(entry_year, entry_age, term_age) %>% 
    left_join(long_term_rate_table) %>% 
    left_join(normal_retire_rate_tier_1_table %>% rename(normal_retire_rate_tier_1 = normal_retire_rate), by = c("term_age" = "age")) %>% 
    left_join(normal_retire_rate_tier_2_table %>% rename(normal_retire_rate_tier_2 = normal_retire_rate), by = c("term_age" = "age")) %>% 
    left_join(early_retire_rate_tier_1_table %>% rename(early_retire_rate_tier_1 = early_retire_rate), by = c("term_age" = "age")) %>% 
    left_join(early_retire_rate_tier_2_table %>% rename(early_retire_rate_tier_2 = early_retire_rate), by = c("term_age" = "age")) %>% 
    group_by(entry_year, entry_age) %>% 
    fill(contains("retire_rate"), .direction="downup") %>% 
    ungroup() %>% 
    mutate(
      tier_at_term_age = get_tier(class_name, entry_year, term_age, yos),
      separation_rate = case_when(
        tier_at_term_age %in% c("tier_3_norm", "tier_2_norm") ~ normal_retire_rate_tier_2,
        tier_at_term_age %in% c("tier_3_early", "tier_2_early") ~ early_retire_rate_tier_2,
        tier_at_term_age == "tier_1_norm" ~ normal_retire_rate_tier_1,
        tier_at_term_age == "tier_1_early" ~ early_retire_rate_tier_1,
        str_detect(tier_at_term_age, "vested") ~ term_rate
      )
    ) %>% 
    group_by(entry_year, entry_age) %>% 
    mutate(
      remaining_prob = cumprod(1 - lag(separation_rate, default=0)),
      separation_prob = lag(remaining_prob, default = 1) - remaining_prob
    ) %>% 
    ungroup() %>% 
    select(entry_year, entry_age, term_age, yos, term_year, separation_rate, remaining_prob, separation_prob)
  
  return(sep_rate_table)
}

regular_separation_rate_table <- get_separation_table("regular")
special_separation_rate_table <- get_separation_table("special")
admin_separation_rate_table <- get_separation_table("admin")
eco_separation_rate_table <- get_separation_table("eco")
eso_separation_rate_table <- get_separation_table("regular")
judges_separation_rate_table <- get_separation_table("judges")
senior_management_separation_rate_table <- get_separation_table("senior management")




##############################################################################################################################
##################################################################
##                    Benefit Model Function                    ##
##################################################################

# class_name = class_name_
# dr_current = dr_current_
# dr_new = dr_new_
# cola_tier_1_active = cola_tier_1_active_
# cola_tier_2_active = cola_tier_2_active_
# cola_tier_3_active = cola_tier_3_active_
# cola_current_retire = cola_current_retire_
# cola_current_retire_one = cola_current_retire_one_
# one_time_cola = one_time_cola_
# retire_refund_ratio = retire_refund_ratio_
# cal_factor = cal_factor_

get_benefit_data <- function(
    class_name = class_name_,
    dr_current = dr_current_,
    dr_new = dr_new_,
    cola_tier_1_active_constant = cola_tier_1_active_constant_,
    cola_tier_1_active = cola_tier_1_active_,
    cola_tier_2_active = cola_tier_2_active_,
    cola_tier_3_active = cola_tier_3_active_,
    cola_current_retire = cola_current_retire_,
    cola_current_retire_one = cola_current_retire_one_,
    one_time_cola = one_time_cola_,
    retire_refund_ratio = retire_refund_ratio_,
    cal_factor = cal_factor_
) {
  
  class_name <- str_replace(class_name, " ", "_")
  
  assign("entrant_profile_table", get(paste0(class_name, "_entrant_profile_table")))
  assign("salary_headcount_table", get(paste0(class_name, "_salary_headcount_table")))
  assign("mort_table", get(paste0(class_name, "_mort_table")))
  assign("mort_retire_table", get(paste0(class_name, "_mort_retire_table")))
  assign("sep_rate_table", get(paste0(class_name, "_separation_rate_table")))
  
  class_salary_growth_table <- salary_growth_table %>% 
    select(yos, contains(class_name)) %>% 
    rename(cumprod_salary_increase = 2)

  #Create a long-form table of entry year, entry age, and yos and merge with salary data
  #Note that "age" in the salary_table is active age
  salary_benefit_table <- expand_grid(entry_year = entry_year_range_, entry_age = entrant_profile_table$entry_age, yos = yos_range_) %>% 
    mutate(
      term_age = entry_age + yos,
      # term_year = entry_year + yos,
      tier_at_term_age = get_tier(class_name, entry_year, term_age, yos)
      ) %>% 
    filter(term_age <= max_age_) %>% 
    arrange(entry_year, entry_age, yos) %>% 
    left_join(entrant_profile_table, by = "entry_age") %>% 
    left_join(class_salary_growth_table, by = "yos") %>% 
    #Join salary_head_count_table by entry_year and entry_age only to get historical entry_salary
    left_join(salary_headcount_table %>% select(entry_year, entry_age, entry_salary), by = c("entry_year", "entry_age")) %>%
    mutate(
      salary = if_else(entry_year <= max(salary_headcount_table$entry_year), entry_salary * cumprod_salary_increase,
                       start_sal * cumprod_salary_increase * (1 + payroll_growth_)^(entry_year - max(salary_headcount_table$entry_year))),
      fas_period = if_else(str_detect(tier_at_term_age, "tier_1"), 5, 8)
    ) %>% 
    group_by(entry_year, entry_age) %>% 
    mutate(
      fas = baseR.rollmean(salary, fas_period),
      db_ee_cont = db_ee_cont_rate_ * salary,
      db_ee_balance = get_cum_fv(db_ee_interest_rate_, db_ee_cont),
    ) %>% 
    ungroup() %>% 
    filter(!is.na(salary))

  
  #Survival Probability and Annuity Factor for active members
  ann_factor_table <- mort_table %>% 
    #Semi join the salary_benefit_able to reduce the size of the data that needs to be calculated
    semi_join(salary_benefit_table, by = c("entry_year", "entry_age")) %>%
    mutate(
      dr = if_else(str_detect(tier_at_dist_age, "tier_3"), dr_new, dr_current),
      yos_b4_2011 = pmin(pmax(2011 - entry_year, 0), yos),
      cola = case_when(
        #Tier 1 cola (current policy) = 3% * YOS before 2011 / Total YOS
        str_detect(tier_at_dist_age, "tier_1") & cola_tier_1_active_constant == "no" ~ if_else(yos > 0, cola_tier_1_active * yos_b4_2011 / yos, 0),
        str_detect(tier_at_dist_age, "tier_1") & cola_tier_1_active_constant == "yes" ~ cola_tier_1_active,
        str_detect(tier_at_dist_age, "tier_2") ~ cola_tier_2_active,
        str_detect(tier_at_dist_age, "tier_3") ~ cola_tier_3_active
      )
    ) %>% 
    group_by(entry_year, entry_age, yos) %>% 
    mutate(
      cum_dr = cumprod(1 + lag(dr, default = 0)),
      cum_mort = cumprod(1 - lag(mort_final, default = 0)),
      cum_cola = cumprod(1 + lag(cola, default = 0)),
      cum_mort_dr = cum_mort / cum_dr,
      cum_mort_dr_cola = cum_mort_dr * cum_cola,
      #ann_factor below is the annuity factor at distribution (retirement) age
      ann_factor = rev(cumsum(rev(cum_mort_dr_cola))) / cum_mort_dr_cola
    ) %>% 
    ungroup()
  
  #Survival Probability and Annuity Factor for current retirees
  ann_factor_retire_table <- mort_retire_table %>% 
    mutate(
      dr = dr_current,
      cola_type = if_else(one_time_cola == T, "one_time", "normal"),
      cola = if_else(cola_type == "one_time", if_else(year == new_year_, cola_current_retire_one, 0),
                     cola_current_retire)
    ) %>% 
    group_by(base_age) %>% 
    mutate(
      cum_dr = cumprod(1 + lag(dr, default = 0)),
      cum_mort = cumprod(1 - lag(mort_final, default = 0)),
      cum_mort_dr = cum_mort / cum_dr,
      ann_factor_retire = annfactor(cum_mort_dr, cola_vec = cola, one_time_cola = one_time_cola)
    )

  benefit_table <- ann_factor_table %>%
    mutate(
      term_age = entry_age + yos, .before = term_year,
      class_name = class_name,
      is_norm_retire_elig = str_detect(tier_at_dist_age, "norm")
    ) %>%
    #dist_age is distribution age, and dist_year is distribution year.
    #distribution age means the age when the member starts to accept benefits (either a refund or a pension)
    left_join(salary_benefit_table,
              by = c("entry_year", "entry_age", "yos", "term_age")) %>%
    mutate(
      ben_mult = if_else(str_detect(tier_at_dist_age, "tier_1"),
                         if_else(class_name == "regular", 
                                 case_when(
                                   (dist_age >= 65 & yos >= 6) | (yos >= 33) ~ 0.0168,
                                   (dist_age >= 64 & yos >= 6) | (yos >= 32) ~ 0.0165,
                                   (dist_age >= 63 & yos >= 6) | (yos >= 31) ~ 0.0163,
                                   (dist_age >= 62 & yos >= 6) | (yos >= 30) ~ 0.0160,
                                   str_detect(tier_at_dist_age, "early") ~ 0.0160
                                 ),
                                 if_else(class_name == "special", if_else(dist_year <= 1974, 0.02, 0.03),
                                         if_else(class_name == "admin", 
                                                 case_when(
                                                   (dist_age >= 58 & yos >= 6) | (yos >= 28) ~ 0.0168,
                                                   (dist_age >= 57 & yos >= 6) | (yos >= 27) ~ 0.0165,
                                                   (dist_age >= 56 & yos >= 6) | (yos >= 26) ~ 0.0163,
                                                   (dist_age >= 55 & yos >= 6) | (yos >= 25) ~ 0.0160,
                                                   str_detect(tier_at_dist_age, "early") ~ 0.0160
                                                 ),
                                                 if_else(class_name %in% c("eco", "eso"), 0.03,
                                                         if_else(class_name == "judges", 0.0333, if_else(class_name == "senior_management", 0.02, NA)
                                                         )
                                                 )
                                         )
                                 )
                         ),
                         if_else(str_detect(tier_at_dist_age, "tier_2"),
                                 if_else(class_name == "regular",
                                         case_when(
                                           (dist_age >= 68 & yos >= 8) | (yos >= 36) ~ 0.0168,
                                           (dist_age >= 67 & yos >= 8) | (yos >= 35) ~ 0.0165,
                                           (dist_age >= 66 & yos >= 8) | (yos >= 34) ~ 0.0163,
                                           (dist_age >= 65 & yos >= 8) | (yos >= 33) ~ 0.0160,
                                           str_detect(tier_at_dist_age, "early") ~ 0.0160
                                         ),
                                         if_else(class_name == "special", if_else(dist_year <= 1974, 0.02, 0.03),
                                                 if_else(class_name == "admin",
                                                         case_when(
                                                           (dist_age >= 63 & yos >= 8) | (yos >= 33) ~ 0.0168,
                                                           (dist_age >= 62 & yos >= 8) | (yos >= 32) ~ 0.0165,
                                                           (dist_age >= 61 & yos >= 8) | (yos >= 31) ~ 0.0163,
                                                           (dist_age >= 60 & yos >= 8) | (yos >= 30) ~ 0.0160,
                                                           str_detect(tier_at_dist_age, "early") ~ 0.0160
                                                         ),
                                                         if_else(class_name %in% c("eco", "eso"), 0.03,
                                                                 if_else(class_name == "judges", 0.0333, if_else(class_name == "senior_management", 0.02, NA)
                                                                 )
                                                         )
                                                 )
                                         )
                                 ),
                                 if_else(str_detect(tier_at_dist_age, "tier_3"),
                                         if_else(class_name == "regular",
                                                 case_when(
                                                   (dist_age >= 68 & yos >= 8) | (yos >= 36) ~ 0.0168,
                                                   (dist_age >= 67 & yos >= 8) | (yos >= 35) ~ 0.0165,
                                                   (dist_age >= 66 & yos >= 8) | (yos >= 34) ~ 0.0163,
                                                   (dist_age >= 65 & yos >= 8) | (yos >= 33) ~ 0.0160,
                                                   str_detect(tier_at_dist_age, "early") ~ 0.0160
                                                 ),
                                                 if_else(class_name == "special", if_else(dist_year <= 1974, 0.02, 0.03),
                                                         if_else(class_name == "admin",
                                                                 case_when(
                                                                   dist_age >= 63 & yos >= 8 ~ 0.0168,
                                                                   dist_age >= 62 & yos >= 8 ~ 0.0165,
                                                                   dist_age >= 61 & yos >= 8 ~ 0.0163,
                                                                   dist_age >= 60 & yos >= 8 ~ 0.0160,
                                                                   str_detect(tier_at_dist_age, "early") ~ 0.0160
                                                                 ),
                                                                 if_else(class_name %in% c("eco", "eso"), 0.03,
                                                                         if_else(class_name == "judges", 0.0333, if_else(class_name == "senior_management", 0.02, NA)
                                                                         )
                                                                 )
                                                         )
                                                 )
                                         ), NA)
                         )
      ),
      
      reduce_factor = if_else(str_detect(tier_at_dist_age, "norm"), 1,
                              if_else(str_detect(tier_at_dist_age, "early"),
                                      if_else(class_name == "special",
                                              case_when(
                                                str_detect(tier_at_dist_age, "tier_1") ~ (1 - 0.05*(55 - dist_age)),
                                                str_detect(tier_at_dist_age, "tier_2") ~ (1 - 0.05*(60 - dist_age)),
                                                str_detect(tier_at_dist_age, "tier_3") ~ (1 - 0.05*(60 - dist_age))
                                              ),
                                              case_when(
                                                str_detect(tier_at_dist_age, "tier_1") ~ (1 - 0.05*(62 - dist_age)),
                                                str_detect(tier_at_dist_age, "tier_2") ~ (1 - 0.05*(65 - dist_age)),
                                                str_detect(tier_at_dist_age, "tier_3") ~ (1 - 0.05*(65 - dist_age))
                                              )
                                      ), NA
                              )
      ),
      
      db_benefit = yos * ben_mult * fas * reduce_factor,
      
      #cal_factor is a calibration factor added to match the normal cost from the val report
      db_benefit = db_benefit * cal_factor,
      
      #calculate the annuity factor at termination day
      ann_factor_term = ann_factor * cum_mort_dr,
      
      #calculate the actuarial present value of future DB benefits at termination day (discount the annual DB benefits back to termination day)
      pvfb_db_at_term_age = db_benefit * ann_factor_term
      
    )

 
  #Determine the ultimate distribution age for each member (the age when they're assumed to retire/get a refund, given their termination age)
  dist_age_table <- benefit_table %>% 
    group_by(entry_year, entry_age, term_age) %>% 
    summarise(
      earliest_norm_retire_age = n() - sum(is_norm_retire_elig) + min(dist_age),
      term_status = tier_at_term_age[1]
    ) %>% 
    ungroup() %>%
    mutate(
      dist_age = if_else(
        str_detect(term_status, "vested") & !str_detect(term_status, "non_vested"), earliest_norm_retire_age, term_age
        )
    ) %>% 
    select(entry_year, entry_age, term_age, dist_age)
  
  #Retain only the final distribution ages in the final_benefit_table
  final_benefit_table <- benefit_table %>% 
    semi_join(dist_age_table) %>% 
    select(entry_year, entry_age, term_age, dist_age, db_benefit, pvfb_db_at_term_age, ann_factor_term) %>% 
    mutate(
      #NA benefit values (because the member is not vested) are replaced with 0
      db_benefit = if_else(is.na(db_benefit), 0, db_benefit),
      pvfb_db_at_term_age = if_else(is.na(pvfb_db_at_term_age), 0, pvfb_db_at_term_age)
    )
  
  ##################################################################################################
  
  ####### Benefit Accrual & Normal Cost #######
  
  benefit_val_table <- salary_benefit_table %>% 
    left_join(final_benefit_table, by = c("entry_year", "entry_age", "term_age")) %>%
    left_join(sep_rate_table) %>%
    mutate(
      #note that the tier below applies at termination age only
      dr = if_else(str_detect(tier_at_term_age, "tier_3"), dr_new, dr_current),
      sep_type = get_sep_type(tier_at_term_age),
      ben_decision = if_else(yos == 0, NA, if_else(sep_type == "retire", "retire",
                                                   if_else(sep_type == "vested", "mix", "refund"))),
      pvfb_db_wealth_at_term_age = case_when(
        sep_type == "retire" ~ pvfb_db_at_term_age,
        sep_type == "vested" ~ (retire_refund_ratio * pvfb_db_at_term_age + (1 - retire_refund_ratio) * db_ee_balance),
        sep_type == "non_vested" ~ db_ee_balance
        )
    ) %>% 
    group_by(entry_year, entry_age) %>%
    mutate(
      #calculate the present value of future DB benefits at current age (discount the annual DB benefits back to current age)
      pvfb_db_wealth_at_current_age = get_pvfb(sep_rate_vec = separation_rate, interest_vec = dr, value_vec = pvfb_db_wealth_at_term_age),
      
      #calculate the present value of future salary at current age (discount the annual salary back to current age)
      pvfs_at_current_age = get_pvfs(remaining_prob_vec = remaining_prob, interest_vec = dr, sal_vec = salary),
      
      #calculate the individual normal cost rate at current age
      indv_norm_cost = pvfb_db_wealth_at_current_age[yos == 0] / pvfs_at_current_age[yos == 0],
      
      #calculate the present value of future normal cost at current age (discount the annual normal cost back to current age)
      pvfnc_db = indv_norm_cost * pvfs_at_current_age
    ) %>% 
    ungroup()
  
  indv_norm_cost_table <- benefit_val_table %>% 
    filter(yos == 0) %>% 
    select(entry_year, entry_age, indv_norm_cost)
    
  
  agg_norm_cost_table <- indv_norm_cost_table %>% 
    left_join(salary_headcount_table, by = c("entry_year", "entry_age")) %>% 
    left_join(salary_benefit_table %>% select(entry_year, entry_age, yos, salary), by = c("entry_year", "entry_age", "yos")) %>% 
    filter(!is.na(count)) %>% 
    summarise(
      agg_normal_cost = sum(indv_norm_cost * salary * count) / sum(salary * count)
    )
  
  output <- list(
    ann_factor_table = ann_factor_table,
    ann_factor_retire_table = ann_factor_retire_table,
    benefit_table = benefit_table,
    final_benefit_table = final_benefit_table,
    benefit_val_table = benefit_val_table,
    indv_norm_cost_table = indv_norm_cost_table,
    agg_norm_cost_table = agg_norm_cost_table
    )
  
  return(output)
}


# regular_benefit_data <- get_benefit_data(class_name = "regular")
# special_benefit_data <- get_benefit_data(class_name = "special")
# eco_benefit_data <- get_benefit_data(class_name = "eco")
# eso_benefit_data <- get_benefit_data(class_name = "eso")
# admin_benefit_data <- get_benefit_data(class_name = "admin")
# judges_benefit_data <- get_benefit_data(class_name = "judges")
# senior_management_benefit_data <- get_benefit_data(class_name = "senior management")
# 
# 
# regular_norm_cost_diff <- regular_val_norm_cost / regular_benefit_data$agg_norm_cost_table[[1]]
# special_norm_cost_diff <- special_val_norm_cost / special_benefit_data$agg_norm_cost_table[[1]]
# admin_norm_cost_diff <- admin_val_norm_cost / admin_benefit_data$agg_norm_cost_table[[1]]
# eco_norm_cost_diff <- eco_val_norm_cost / eco_benefit_data$agg_norm_cost_table[[1]]
# eso_norm_cost_diff <- eso_val_norm_cost / eso_benefit_data$agg_norm_cost_table[[1]]
# judges_norm_cost_diff <- judges_val_norm_cost / judges_benefit_data$agg_norm_cost_table[[1]]
# senior_management_norm_cost_diff <- senior_management_val_norm_cost / senior_management_benefit_data$agg_norm_cost_table[[1]]




