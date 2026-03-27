#################################################################
##                       Workforce Model                       ##
#################################################################

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

get_wf_data <- function(
    class_name = class_name_,
    dr_current = dr_current_,
    dr_new = dr_new_,
    cola_tier_1_active = cola_tier_1_active_,
    cola_tier_2_active = cola_tier_2_active_,
    cola_tier_3_active = cola_tier_3_active_,
    cola_current_retire = cola_current_retire_,
    cola_current_retire_one = cola_current_retire_one_,
    one_time_cola = one_time_cola_,
    retire_refund_ratio = retire_refund_ratio_,
    cal_factor = cal_factor_
) {
  
  #Get benefit data
  benefit_data <- get_benefit_data(
    class_name = class_name,
    dr_current = dr_current,
    dr_new = dr_new,
    cola_tier_1_active = cola_tier_1_active,
    cola_tier_2_active = cola_tier_2_active,
    cola_tier_3_active = cola_tier_3_active,
    cola_current_retire = cola_current_retire,
    cola_current_retire_one = cola_current_retire_one,
    one_time_cola = one_time_cola,
    retire_refund_ratio = retire_refund_ratio,
    cal_factor = cal_factor
  )
  
  class_name <- str_replace(class_name, " ", "_")
  assign("entrant_profile_table", get(paste0(class_name, "_entrant_profile_table")))
  assign("salary_headcount_table", get(paste0(class_name, "_salary_headcount_table")))
  assign("mort_table", get(paste0(class_name, "_mort_table")))
  assign("separation_rate_table", get(paste0(class_name, "_separation_rate_table")))
  
  
  
  #Initialize empty workforce projection arrays
  entry_age_range <- entrant_profile_table$entry_age
  age_range <- min(entry_age_range):max(age_range_)
  year_range <- start_year_:(start_year_ + model_period_)   #test now, fix this later
  term_year_range <- year_range
  retire_year_range <- year_range
  
  
  active_dim <- c(length(entry_age_range), length(age_range), length(year_range))
  active_dim_names <- list(entry_age = entry_age_range, age = age_range, year = year_range)
  
  term_dim <- c(length(entry_age_range), length(age_range), length(year_range), length(term_year_range))
  term_dim_names <- list(entry_age = entry_age_range, age = age_range, year = year_range, term_year = term_year_range)
  
  retire_dim <- c(length(entry_age_range), length(age_range), length(year_range), length(term_year_range), length(retire_year_range))
  retire_dim_names <- list(entry_age = entry_age_range, age = age_range, year = year_range, term_year = term_year_range, retire_year = retire_year_range)
  
  wf_active <- array(0, dim = active_dim, dimnames = active_dim_names)
  wf_term <- array(0, dim = term_dim, dimnames = term_dim_names)
  wf_refund <- wf_term
  wf_retire <- array(0, dim = retire_dim, dimnames = retire_dim_names)
  
  
  #Initial active population
  active_int_df <- expand_grid(entry_age = entry_age_range, age = age_range) %>%
    left_join(salary_headcount_table, by = c("entry_age", "age")) %>%
    replace(is.na(.), 0) %>%
    select(entry_age, age, count)
  
  active_int_matrix <- xtabs(count ~ entry_age + age, active_int_df)
  
  wf_active[,,1] <- active_int_matrix
  
  # active_int_pop <- c(2000, 8000, 8000, 7000, 8000, 9000, 8000, 7000, 6000, 5000)
  # 
  # active_int_ea <- data.frame(ea = SalaryEntry$entry_age, age = SalaryEntry$entry_age, n_active = active_int_pop)
  # 
  # active_int <- expand_grid(ea, age) %>% 
  #   left_join(active_int_ea) %>% 
  #   replace(is.na(.), 0) %>% 
  #   pivot_wider(names_from = age, values_from = n_active) %>% 
  #   select(-1)
  # 
  # wf_active[,,1] <- as.matrix(active_int)
  
  #Position matrix to add new hires
  position_matrix <- expand_grid(entry_age = entry_age_range, age = age_range) %>% 
    mutate(new = if_else(entry_age == age, 1, 0))
  
  position_matrix <- xtabs(new ~ entry_age + age, position_matrix)
  
  ##Create probability array
  
  #Mortality probability array (4 dimensions)
  mort_df_term <- expand_grid(entry_age = entry_age_range, age = age_range, year = year_range, term_year = term_year_range) %>% 
    left_join(mort_table, by = c("entry_age", "age" = "dist_age", "year" = "dist_year", "term_year")) %>% 
    mutate(mort = if_else(is.na(mort_final), 0, mort_final))
  
  mort_array_term <- xtabs(mort ~ entry_age + age + year + term_year, mort_df_term)
  
  #Separation probability array (3 dimensions): 
  sep_df <- expand_grid(entry_age = entry_age_range, age = age_range, year = year_range) %>% 
    mutate(entry_year = year - (age - entry_age)) %>% 
    left_join(separation_rate_table, by = c("entry_age", "age" = "term_age", "entry_year")) %>% 
    select(entry_age, age, year, separation_rate) %>% 
    mutate(separation_rate = if_else(is.na(separation_rate), 0, separation_rate))
  
  sep_array <- xtabs(separation_rate ~ entry_age + age + year, sep_df)
  
  #Refund and retirement probability arrays
  optimal_retire <- benefit_data$benefit_val_table %>% 
    # rename(term_age = Age) %>% 
    select(entry_year, entry_age, term_age, yos, dist_age, ben_decision) %>% 
    mutate(refund = case_when(ben_decision == "refund" ~ 1,     #use case_when instead of ifselse to handle NA values better
                              ben_decision == "mix" ~ 1 - retire_refund_ratio,
                              .default = 0),
           retire = case_when(ben_decision == "retire" ~ 1,
                              ben_decision == "mix" ~ 1,
                              .default = 0),
           refund_age = term_age)
  
  #Retire probability array (4 dimensions)
  retire_df <- expand_grid(entry_age = entry_age_range, age = age_range, year = year_range, term_year = term_year_range) %>% 
    mutate(
      entry_year = year - (age - entry_age),
      term_age = age - (year - term_year),
      yos = term_age - entry_age) %>% 
    filter(year - term_year >= 0, yos >= 0) %>% 
    left_join(optimal_retire, by = c("entry_age",
                                     "age" = "dist_age",
                                     "entry_year",
                                     "term_age",
                                     "yos")) %>% 
    mutate(retire = if_else(is.na(retire), 0, retire))
  
  retire_array <- xtabs(retire ~ entry_age + age + year + term_year, retire_df) 
  
  #Refund probability array (4 dimensions). Note that employees get refunds in the same year they get terminated. 
  refund_df <- expand_grid(entry_age = entry_age_range, age = age_range, year = year_range, term_year = term_year_range) %>% 
    mutate(
      entry_year = year - (age - entry_age),
      term_age = age - (year - term_year),
      yos = term_age - entry_age
      ) %>% 
    filter(year - term_year >= 0, yos >= 0) %>% 
    left_join(optimal_retire, by = c("entry_age",
                                     "age" = "refund_age",
                                     "entry_year",
                                     "term_age",
                                     "yos")) %>% 
    mutate(refund = if_else(is.na(refund), 0, refund))
  
  refund_array <- xtabs(refund ~ entry_age + age + year + term_year, refund_df)
  
  #Transition matrix to shift the population to the right by 1 age after 1 year
  TM <-  diag(length(age_range) + 1)[-1, -(length(age_range) + 1)] 
  
  
  #Workforce projection
  for (i in 2:length(year_range)) {
    active2term <- wf_active[,,i-1] * sep_array[,,i-1]   #calculate the # of newly terminated actives. 2-dimensional array
    
    wf_active[,,i] <- (wf_active[,,i-1] - active2term) %*% TM  #deduct terminated members from the active workforce and shift the wf_active matrix to the right by one year
    
    new_entrants <- add_new_entrants(g = pop_growth_, ne_dist = entrant_profile_table$entrant_dist, wf1 = wf_active[,,i-1],
                                     wf2 = wf_active[,,i], ea = entry_age_range, age = age_range, position_matrix = position_matrix)  #new entrants matrix to be added to the active workforce

    wf_active[,,i] = wf_active[,,i] + new_entrants  #add new entrants
    
    term2death <- wf_term[,,i-1,] * mort_array_term[,,i-1,] #3-dimensional array
    
    wf_term[,,i,] <- apply(wf_term[,,i-1,] - term2death, 3, function(x) x %*% TM) %>% array(term_dim[-3]) 
    
    wf_term[,,i,i] <- active2term %*% TM   #add newly terminated members the term population
    
    term2refund <- wf_term[,,i,i] * refund_array[,,i,i]  #calculate the # of newly refunded members. 2-dimensional array
    
    wf_term[,,i,i] <- wf_term[,,i,i] - term2refund
    
    wf_refund[,,i,i] <- term2refund
    
    term2retire <- wf_term[,,i,] * retire_array[,,i,]  #calculate the # of newly retired members. 3-dimensional array
    
    wf_term[,,i,] <- wf_term[,,i,] - term2retire
    
    retire2death <- apply(wf_retire[,,i-1,,], 4, function(x) x * mort_array_term[,,i-1,]) %>% array(retire_dim[-3])   #4-dimensional array
    
    wf_retire[,,i,,] <- apply(wf_retire[,,i-1,,] - retire2death, c(3,4), function(x) x %*% TM) %>% array(retire_dim[-3])
    
    wf_retire[,,i,,i] <- term2retire
    
  }
  
  
  #####Convert the multidimensional arrays into data frames 
  wf_active_df <- data.frame(expand.grid(entry_age = entry_age_range, 
                                         age = age_range, 
                                         year = year_range), 
                             n_active = as.vector(wf_active)) %>% filter(age >= entry_age)
  
  wf_term_df <- data.frame(expand.grid(entry_age = entry_age_range, 
                                       age = age_range, 
                                       year = year_range, 
                                       term_year = term_year_range), n_term = as.vector(wf_term)) %>% 
    filter(age >= entry_age, year >= term_year)
  
  wf_refund_df <- data.frame(expand.grid(entry_age = entry_age_range, 
                                         age = age_range, 
                                         year = year_range, 
                                         term_year = term_year_range), n_refund = as.vector(wf_refund)) %>% 
    filter(age >= entry_age, year >= term_year)
  
  #Since the wf_retire array is too big to handle using the above method, we need to split it into smaller parts for processing
  wf_retire_list <- list()  #empty list to save retire workforce data in the for loop
  
  for (i in seq_along(entrant_profile_table$entry_age)) {
    wf_retire_name <- paste0("wf_retire_", entrant_profile_table$entry_age[i])
    assign(wf_retire_name, wf_retire[i,,,,])
    wf_retire_i <- data.table(CJ(retire_year = retire_year_range, term_year = term_year_range, year = year_range, age = age_range), n_retire = as.vector(get(wf_retire_name)))[n_retire > 0,] %>% 
      mutate(entry_age = entrant_profile_table$entry_age[i])
    assign(wf_retire_name, wf_retire_i)   #do this to save memory space
    wf_retire_list <- append(wf_retire_list, list(get(wf_retire_name)))
  }
  
  #Combine all retire data frames from the retire list into one retire data frame 
  wf_retire_df <- rbindlist(wf_retire_list) %>% 
    select(entry_age, age, year, term_year, retire_year, n_retire)
  
  
  wf_data <- list(wf_active_df = wf_active_df,
                  wf_term_df = wf_term_df,
                  wf_refund_df = wf_refund_df,
                  wf_retire_df = wf_retire_df)
  
  saveRDS(wf_data, paste0(class_name, "_wf_data.rds"))
  
}




