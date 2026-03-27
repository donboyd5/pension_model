#################################################################
##                        Funding Model                        ##
#################################################################


####Data preparation
#Create 9 empty data frames from the init_funding_data (representing 7 classes, DROP, and FRS system), then put them in a list to store funding outputs for these entities
get_funding_table <- function(class_name) {
  funding_table <- init_funding_data %>% 
    filter(class == class_name) %>% 
    select(-class) %>%
    add_row(year = (start_year_ + 1):(start_year_ + model_period_))
  
  funding_table[is.na(funding_table)] <- 0
  
  return(funding_table)
}

class_names <- init_funding_data$class
funding_list <- lapply(class_names, get_funding_table)
names(funding_list) <- class_names


#Summarize current amortization layers
current_amort_layers_table <- current_amort_layers_table_ %>% 
  mutate(amo_period = if_else(amo_period == "n/a", "20", amo_period),
         amo_period = as.numeric(amo_period)) %>% 
  group_by(class, amo_period) %>%
  summarise(amo_balance = sum(amo_balance)) %>% 
  #make sure that the amo periods are arranged in descending order
  arrange(class, desc(amo_period)) %>% 
  ungroup()

#More groups for class names:
class_names_no_drop_frs <- class_names[!class_names %in% c("drop", "frs")]
class_names_no_frs <- class_names[!class_names %in% c("frs")]



################### Model function starts here ####################
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
# #inputs below are for the liability model
# non_special_db_new_ratio = non_special_db_new_ratio_
# special_db_new_ratio = special_db_new_ratio_
# #inputs below are for the funding model
# return_scen = return_scen_
# model_return = model_return_
# amo_period_new = amo_period_new_
# amo_pay_growth = amo_pay_growth_
# amo_method = amo_method_


get_funding_data <- function(
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
    cal_factor = cal_factor_,
    #inputs below are for the liability model
    non_special_db_new_ratio = non_special_db_new_ratio_,
    special_db_new_ratio = special_db_new_ratio_,
    #inputs below are for the funding model
    return_scen = return_scen_,
    model_return = model_return_,
    amo_period_new = amo_period_new_,
    amo_pay_growth = amo_pay_growth_,
    amo_method = amo_method_
) {
  
  
  ####Produce liability outputs for each class (except DROP and FRS system)
  
  #Use mclapply to run the liability model in parallel. May not work properly with Windows OS or API. Switch back to lapply if needed. When working, mclapply will be about twice as fast as lapply.
  liability_list <- mclapply(X = class_names_no_drop_frs, FUN = get_liability_data, mc.cores = 1, # changed from 4 to 1 to run on Windows
                             dr_current = dr_current,
                             dr_new = dr_new,
                             cola_tier_1_active_constant = cola_tier_1_active_constant,
                             cola_tier_1_active = cola_tier_1_active,
                             cola_tier_2_active = cola_tier_2_active,
                             cola_tier_3_active = cola_tier_3_active,
                             cola_current_retire = cola_current_retire,
                             cola_current_retire_one = cola_current_retire_one,
                             one_time_cola = one_time_cola,
                             retire_refund_ratio = retire_refund_ratio,
                             cal_factor = cal_factor,
                             #inputs below are for the liability model
                             non_special_db_new_ratio = non_special_db_new_ratio,
                             special_db_new_ratio = special_db_new_ratio)
  
  names(liability_list) <- class_names_no_drop_frs
  
  #Create a "liability" data for the DROP plan
  #This is a makeshift solution for now. Proper modeling of the DROP plan will be done in the future.
  # drop_liability_output <- funding_list[["drop"]]
  
  
      
  
  ####Model calibration 
  for (class in class_names_no_drop_frs) {
    fund_data <- funding_list[[class]]
    liab_data <- liability_list[[class]]
    #payroll calibration
    fund_data$payroll_db_legacy_ratio <- lag(liab_data$payroll_db_legacy_est / liab_data$total_payroll_est) #use lag to align with the funding mechanism
    fund_data$payroll_db_new_ratio <- lag(liab_data$payroll_db_new_est / liab_data$total_payroll_est)
    fund_data$payroll_dc_legacy_ratio <- lag(liab_data$payroll_dc_legacy_est / liab_data$total_payroll_est)
    fund_data$payroll_dc_new_ratio <- lag(liab_data$payroll_dc_new_est / liab_data$total_payroll_est)
    
    #normal cost calibration/projection
    nc_cal <- get(str_replace(paste0(class, "_nc_cal_"), " ", "_"))
    fund_data$nc_rate_db_legacy <- lag(liab_data$nc_rate_db_legacy_est * nc_cal)
    fund_data$nc_rate_db_new <- lag(liab_data$nc_rate_db_new_est * nc_cal)
    
    #accrued liability calibration
    fund_data$aal_legacy[1] <- liab_data$aal_legacy_est[1]
    fund_data$total_aal[1] <- liab_data$total_aal_est[1]
    fund_data$ual_ava_legacy[1] <- fund_data$aal_legacy[1] - fund_data$ava_legacy[1]
    fund_data$total_ual_ava[1] <- fund_data$total_aal[1] - fund_data$total_ava[1]
    
    
    funding_list[[class]] <- fund_data
  }
  
  
  ####Set up amo period sequences
  #Determine the number of columns for the amo period tables
  amo_col_num <- max(current_amort_layers_table$amo_period, amo_period_new + funding_lag_)
  
  #Create two lists, one for the current hire amo periods, and one for new hire amo periods
  #Current hire amo periods list construction:
  get_current_hire_amo_period_table <- function(class_name) {
    class_amo_layers_table <- current_amort_layers_table %>% 
      filter(class == class_name)
    
    current_periods <- class_amo_layers_table$amo_period
    future_periods <- amo_period_new + funding_lag_
    length(current_periods) <- amo_col_num
    length(future_periods) <- amo_col_num
    
    current_hire_amo_period_table <- rbind(current_periods, matrix(future_periods, 
                                                                   nrow = model_period_,
                                                                   ncol = amo_col_num,
                                                                   byrow = T))
    
    rownames(current_hire_amo_period_table) <- NULL         #Remove row names
    
    #Put the amo periods on diagonal rows
    for (i in 2:nrow(current_hire_amo_period_table)) {
      for (j in 2:ncol(current_hire_amo_period_table)) {
        current_hire_amo_period_table[i,j] <- max(current_hire_amo_period_table[i-1,j-1] - 1, 0)
      }
    }
    
    #Turn all NAs in the table to 0s
    current_hire_amo_period_table[is.na(current_hire_amo_period_table)] <- 0
    
    return(current_hire_amo_period_table)
  }
  
  
  current_hire_amo_period_list <- lapply(class_names_no_frs, get_current_hire_amo_period_table)
  names(current_hire_amo_period_list) <- class_names_no_frs
  
  
  #Future hire amo periods list construction:
  get_future_hire_amo_period_table <- function(class_name) {
    future_periods <- amo_period_new + funding_lag_
    length(future_periods) <- amo_col_num
    
    future_hire_amo_period_table <- matrix(future_periods, 
                                           nrow = model_period_ + 1,
                                           ncol = amo_col_num,
                                           byrow = T) 
    
    #Put the amo periods on diagonal rows
    for (i in 2:nrow(future_hire_amo_period_table)) {
      for (j in 2:ncol(future_hire_amo_period_table)) {
        future_hire_amo_period_table[i,j] <- max(future_hire_amo_period_table[i-1,j-1] - 1, 0)
      }
    }
    
    #Turn all NAs in the table to 0s
    future_hire_amo_period_table[is.na(future_hire_amo_period_table)] <- 0
    
    return(future_hire_amo_period_table)
  }
  
  future_hire_amo_period_list <- lapply(class_names_no_frs, get_future_hire_amo_period_table)
  names(future_hire_amo_period_list) <- class_names_no_frs
  
  
  #Level % or level $ for debt amortization 
  if(amo_method == "level $"){
    amo_pay_growth <- 0
  }
  
  ####Set up the UAAL layer and amo payment tables for current members and initialize the first UAAL layer and amo payments
  #UAAL layers tables for current members
  get_current_hire_debt_layer_table <- function(class_name) {
    current_hire_debt_layer_table <- matrix(0, nrow = model_period_ + 1, ncol = amo_col_num + 1)
    
    current_hire_debt_layers <- current_amort_layers_table %>% 
      filter(class == class_name) %>% 
      arrange(desc(amo_period)) %>% 
      pull(amo_balance)
    
    current_hire_debt_layer_table[1,1:length(current_hire_debt_layers)] <- current_hire_debt_layers
    
    return(current_hire_debt_layer_table)
  }
  
  
  current_hire_debt_layer_list <- lapply(class_names_no_frs, get_current_hire_debt_layer_table)
  names(current_hire_debt_layer_list) <- class_names_no_frs
  
  #Amo payment tables for current members
  get_current_hire_amo_payment_table <- function(class_name) {
    
    current_hire_amo_payment_table <- matrix(0, nrow = model_period_ + 1, ncol = amo_col_num)
    init_debt_layers <- current_hire_debt_layer_list[[class_name]][1,1:amo_col_num]
    amo_periods <- current_hire_amo_period_list[[class_name]][1,1:amo_col_num]
    
    current_hire_amo_payment_table[1,1:amo_col_num] <- get_pmt(pv = init_debt_layers,
                                                               r = dr_old_,
                                                               g = amo_pay_growth,
                                                               nper = amo_periods,
                                                               t = 0.5)
    if (funding_lag_ > 0) {
      current_hire_amo_payment_table[1,1:funding_lag_] <- 0
    }
    
    return(current_hire_amo_payment_table)
  }
  
  current_hire_amo_payment_list <- lapply(class_names_no_frs, get_current_hire_amo_payment_table)
  names(current_hire_amo_payment_list) <- class_names_no_frs
    
  ####Set up the UAL layer and amo payment tables for new members
  #UAAL layers tables for new members
  get_future_hire_debt_layer_table <- function(class_name) {
    future_hire_debt_layer_table <- matrix(0, nrow = model_period_ + 1, ncol = amo_col_num + 1)
    return(future_hire_debt_layer_table)
  }
  
  future_hire_debt_layer_list <- lapply(class_names_no_frs, get_future_hire_debt_layer_table)
  names(future_hire_debt_layer_list) <- class_names_no_frs
  
  #Amo payment tables for new members
  get_future_hire_amo_payment_table <- function(class_name) {
    future_hire_amo_payment_table <- matrix(0, nrow = model_period_ + 1, ncol = amo_col_num)
    return(future_hire_amo_payment_table)
  }
  
  future_hire_amo_payment_list <- lapply(class_names_no_frs, get_future_hire_amo_payment_table)
  names(future_hire_amo_payment_list) <- class_names_no_frs
  
  
  #Set return values for "model" and "assumption" scenarios
  #Set 2023 returns and update "model" and "assumption" scenarios
  return_scenarios[return_scenarios$year == 2023, 2:6] <- return_2023_
  return_scenarios$model[return_scenarios$year > 2023] <- model_return
  return_scenarios$assumption[return_scenarios$year > 2023] <- dr_current
  
  
  #Return scenario
  # return_scen <- "recur_recession"
  return_scen_index <- which(colnames(return_scenarios) == return_scen)
  

  ########## Main for loop ##########
  #Key strategy: Loop through each year, then each class. The class loop should exclude FRS, and may exclude DROP depending on the calculations
  
  for (i in 2:nrow(funding_list[[1]])) {
    frs_fund <- funding_list$frs
    for (class in class_names_no_drop_frs) {
      #Do the assignment below to declutter the code
      class_fund <- funding_list[[class]]
      class_liab <- liability_list[[class]]
      
      #Payroll projection
      class_fund$total_payroll[i] <- class_fund$total_payroll[i-1] * (1 + payroll_growth_)
      class_fund$payroll_db_legacy[i] <- class_fund$total_payroll[i] * class_fund$payroll_db_legacy_ratio[i]
      class_fund$payroll_db_new[i] <- class_fund$total_payroll[i] * class_fund$payroll_db_new_ratio[i]
      class_fund$payroll_dc_legacy[i] <- class_fund$total_payroll[i] * class_fund$payroll_dc_legacy_ratio[i]
      class_fund$payroll_dc_new[i] <- class_fund$total_payroll[i] * class_fund$payroll_dc_new_ratio[i]
      
      frs_fund$total_payroll[i] <- frs_fund$total_payroll[i] + class_fund$total_payroll[i]
      frs_fund$payroll_db_legacy[i] <- frs_fund$payroll_db_legacy[i] + class_fund$payroll_db_legacy[i]
      frs_fund$payroll_db_new[i] <- frs_fund$payroll_db_new[i] + class_fund$payroll_db_new[i]
      frs_fund$payroll_dc_legacy[i] <- frs_fund$payroll_dc_legacy[i] + class_fund$payroll_dc_legacy[i]
      frs_fund$payroll_dc_new[i] <- frs_fund$payroll_dc_new[i] + class_fund$payroll_dc_new[i]
      
      #Benefit payments and refunds projection
      class_fund$ben_payment_legacy[i] <- class_liab$retire_ben_db_legacy_est[i] + class_liab$retire_ben_current_est[i] + class_liab$retire_ben_term_est[i]
      class_fund$refund_legacy[i] <- class_liab$refund_db_legacy_est[i]
      class_fund$ben_payment_new[i] <- class_liab$retire_ben_db_new_est[i]
      class_fund$refund_new[i] <- class_liab$refund_db_new_est[i]
      
      class_fund$total_ben_payment[i] <- class_fund$ben_payment_legacy[i] + class_fund$ben_payment_new[i]
      class_fund$total_refund[i] <- class_fund$refund_legacy[i] + class_fund$refund_new[i]
      
      frs_fund$ben_payment_legacy[i] <- frs_fund$ben_payment_legacy[i] + class_fund$ben_payment_legacy[i]
      frs_fund$refund_legacy[i] <- frs_fund$refund_legacy[i] + class_fund$refund_legacy[i]
      frs_fund$ben_payment_new[i] <- frs_fund$ben_payment_new[i] + class_fund$ben_payment_new[i]
      frs_fund$refund_new[i] <- frs_fund$refund_new[i] + class_fund$refund_new[i]
      
      frs_fund$total_ben_payment[i] <- frs_fund$total_ben_payment[i] + class_fund$total_ben_payment[i]
      frs_fund$total_refund[i] <- frs_fund$total_refund[i] + class_fund$total_refund[i]
      
      #Normal cost projection
      class_fund$nc_legacy[i] <- class_fund$nc_rate_db_legacy[i] * class_fund$payroll_db_legacy[i]
      class_fund$nc_new[i] <- class_fund$nc_rate_db_new[i] * class_fund$payroll_db_new[i]
      class_fund$total_nc_rate[i] <- (class_fund$nc_legacy[i] + class_fund$nc_new[i]) / (class_fund$payroll_db_legacy[i] + class_fund$payroll_db_new[i])
      
      frs_fund$nc_legacy[i] <- frs_fund$nc_legacy[i] + class_fund$nc_legacy[i]
      frs_fund$nc_new[i] <- frs_fund$nc_new[i] + class_fund$nc_new[i]
      frs_fund$total_nc_rate[i] <- (frs_fund$nc_legacy[i] + frs_fund$nc_new[i]) / (frs_fund$payroll_db_legacy[i] + frs_fund$payroll_db_new[i])
      
      #Accrued liability projection
      class_fund$liability_gain_loss_legacy[i] <- class_liab$liability_gain_loss_legacy_est[i]
      class_fund$liability_gain_loss_new[i] <- class_liab$liability_gain_loss_new_est[i]
      class_fund$total_liability_gain_loss[i] <- class_liab$total_liability_gain_loss_est[i]
      
      class_fund$aal_legacy[i] <- class_fund$aal_legacy[i-1] * (1 + dr_current) + (class_fund$nc_legacy[i] - class_fund$ben_payment_legacy[i] - class_fund$refund_legacy[i]) * (1 + dr_current)^0.5 + class_fund$liability_gain_loss_legacy[i]
      class_fund$aal_new[i] <- class_fund$aal_new[i-1] * (1 + dr_new) + (class_fund$nc_new[i] - class_fund$ben_payment_new[i] - class_fund$refund_new[i]) * (1 + dr_new)^0.5 + class_fund$liability_gain_loss_new[i]
      class_fund$total_aal[i] <- class_fund$aal_legacy[i] + class_fund$aal_new[i]
      
      frs_fund$lia_gain_loss_legacy[i] <- frs_fund$lia_gain_loss_legacy[i] + class_fund$liability_gain_loss_legacy[i]
      frs_fund$lia_gain_loss_new[i] <- frs_fund$lia_gain_loss_new[i] + class_fund$liability_gain_loss_new[i]
      frs_fund$total_lia_gain_loss[i] <- frs_fund$total_lia_gain_loss[i] + class_fund$total_liability_gain_loss[i]
      
      frs_fund$aal_legacy[i] <- frs_fund$aal_legacy[i] + class_fund$aal_legacy[i]
      frs_fund$aal_new[i] <- frs_fund$aal_new[i] + class_fund$aal_new[i]
      frs_fund$total_aal[i] <- frs_fund$total_aal[i] + class_fund$total_aal[i]
      
      #Assign the class outputs back to the funding_list
      funding_list[[class]] <- class_fund
    
    }
    
    ####Process DROP's payroll, benefit payments, normal cost, and accrued liability (note that this is a makeshift method for now). Proper modeling of DROP will be done in the future.
    drop_fund <- funding_list$drop
    regular_fund <- funding_list$regular
  
    #DROP payroll projection (no DC payroll for DROP)
    drop_fund$total_payroll[i] <- drop_fund$total_payroll[i-1] * (1 + payroll_growth_)
    drop_fund$payroll_db_legacy[i] <- drop_fund$total_payroll[i] * (regular_fund$payroll_db_legacy_ratio[i] + regular_fund$payroll_dc_legacy_ratio[i])
    drop_fund$payroll_db_new[i] <- drop_fund$total_payroll[i] * (regular_fund$payroll_db_new_ratio[i] + regular_fund$payroll_dc_new_ratio[i])
  
    #DROP benefit payments and refunds projection (based on Regular class' benefit payments and refuds)
    drop_fund$total_ben_payment[i] <- drop_fund$total_ben_payment[i-1] * regular_fund$total_ben_payment[i] / regular_fund$total_ben_payment[i-1]
    drop_fund$total_refund[i] <- drop_fund$total_refund[i-1] * regular_fund$total_refund[i] / regular_fund$total_refund[i-1]
    
    drop_fund$ben_payment_legacy[i] <- drop_fund$total_ben_payment[i] * regular_fund$ben_payment_legacy[i] / regular_fund$total_ben_payment[i]
    drop_fund$refund_legacy[i] <- drop_fund$total_refund[i] * regular_fund$refund_legacy[i] / regular_fund$total_refund[i]
    drop_fund$ben_payment_new[i] <- drop_fund$total_ben_payment[i] * regular_fund$ben_payment_new[i] / regular_fund$total_ben_payment[i]
    drop_fund$refund_new[i] <- drop_fund$total_refund[i] * regular_fund$refund_new[i] / regular_fund$total_refund[i]
    
    #DROP normal cost projection (DROP's normal cost rate = FRS's normal cost rate)
    drop_fund$nc_rate_db_legacy[i] <- frs_fund$nc_legacy[i] / frs_fund$payroll_db_legacy[i]
    drop_fund$nc_rate_db_new[i] <- if_else(frs_fund$payroll_db_new[i] == 0, 0, frs_fund$nc_new[i] / frs_fund$payroll_db_new[i])
    
    drop_fund$nc_legacy[i] <- drop_fund$nc_rate_db_legacy[i] * drop_fund$payroll_db_legacy[i]
    drop_fund$nc_new[i] <- drop_fund$nc_rate_db_new[i] * drop_fund$payroll_db_new[i]
    drop_fund$total_nc_rate[i] <- (drop_fund$nc_legacy[i] + drop_fund$nc_new[i]) / (drop_fund$payroll_db_legacy[i] + drop_fund$payroll_db_new[i])
    
    #DROP accrued liability projection
    drop_fund$aal_legacy[i] <- drop_fund$aal_legacy[i-1] * (1 + dr_current) + (drop_fund$nc_legacy[i] - drop_fund$ben_payment_legacy[i] - drop_fund$refund_legacy[i]) * (1 + dr_current)^0.5 + drop_fund$liability_gain_loss_legacy[i]
    drop_fund$aal_new[i] <- drop_fund$aal_new[i-1] * (1 + dr_new) + (drop_fund$nc_new[i] - drop_fund$ben_payment_new[i] - drop_fund$refund_new[i]) * (1 + dr_new)^0.5 + drop_fund$liability_gain_loss_new[i]
    drop_fund$total_aal[i] <- drop_fund$aal_legacy[i] + drop_fund$aal_new[i]
    
    #Assign the DROP outputs back to the funding_list
    funding_list$drop <- drop_fund
    
    ####Update FRS's numbers after DROP
    #FRS's payroll projection
    frs_fund$total_payroll[i] <- frs_fund$total_payroll[i] + drop_fund$total_payroll[i]
    frs_fund$payroll_db_legacy[i] <- frs_fund$payroll_db_legacy[i] + drop_fund$payroll_db_legacy[i]
    frs_fund$payroll_db_new[i] <- frs_fund$payroll_db_new[i] + drop_fund$payroll_db_new[i]
    
    #FRS's benefit payments and refunds projection
    frs_fund$ben_payment_legacy[i] <- frs_fund$ben_payment_legacy[i] + drop_fund$ben_payment_legacy[i]
    frs_fund$refund_legacy[i] <- frs_fund$refund_legacy[i] + drop_fund$refund_legacy[i]
    frs_fund$ben_payment_new[i] <- frs_fund$ben_payment_new[i] + drop_fund$ben_payment_new[i]
    frs_fund$refund_new[i] <- frs_fund$refund_new[i] + drop_fund$refund_new[i]
    
    frs_fund$total_ben_payment[i] <- frs_fund$total_ben_payment[i] + drop_fund$total_ben_payment[i]
    frs_fund$total_refund[i] <- frs_fund$total_refund[i] + drop_fund$total_refund[i]
    
    #FRS's normal cost projection
    frs_fund$nc_legacy[i] <- frs_fund$nc_legacy[i] + drop_fund$nc_legacy[i]
    frs_fund$nc_new[i] <- frs_fund$nc_new[i] + drop_fund$nc_new[i]
    frs_fund$total_nc_rate[i] <- (frs_fund$nc_legacy[i] + frs_fund$nc_new[i]) / (frs_fund$payroll_db_legacy[i] + frs_fund$payroll_db_new[i])
    
    frs_fund$nc_rate_db_legacy[i] <- frs_fund$nc_legacy[i] / frs_fund$payroll_db_legacy[i]
    frs_fund$nc_rate_db_new[i] <- if_else(frs_fund$payroll_db_new[i] == 0, 0, frs_fund$nc_new[i] / frs_fund$payroll_db_new[i])
    
    #FRS's accrued liability projection
    frs_fund$aal_legacy[i] <- frs_fund$aal_legacy[i] + drop_fund$aal_legacy[i]
    frs_fund$aal_new[i] <- frs_fund$aal_new[i] + drop_fund$aal_new[i]
    frs_fund$total_aal[i] <- frs_fund$total_aal[i] + drop_fund$total_aal[i]
    
    
    for (class in class_names_no_frs) {
      #Do the assignment below to declutter the code
      class_fund <- funding_list[[class]]
      current_hire_amo_pay_table <- current_hire_amo_payment_list[[class]]
      future_hire_amo_pay_table <- future_hire_amo_payment_list[[class]]
      
      #Normal cost and employee contribution rates
      class_fund$nc_rate_legacy[i] <- class_fund$nc_legacy[i] / class_fund$payroll_db_legacy[i]
      
      if(class_fund$payroll_db_new[i] == 0) {
        class_fund$nc_rate_new[i] <- 0
      } else {
        class_fund$nc_rate_new[i] <- class_fund$nc_new[i] / (class_fund$payroll_db_new[i])  
      }
      
      class_fund$ee_nc_rate_legacy[i] <- db_ee_cont_rate_
      class_fund$ee_nc_rate_new[i] <- db_ee_cont_rate_
      
      #Employer contribution rates (DB)
      class_fund$er_nc_rate_legacy[i] <- class_fund$nc_rate_legacy[i] - class_fund$ee_nc_rate_legacy[i]
      class_fund$er_nc_rate_new[i] <- class_fund$nc_rate_new[i] - class_fund$ee_nc_rate_new[i]
      
      class_fund$amo_rate_legacy[i] <- sum(current_hire_amo_pay_table[i-1,]) / class_fund$payroll_db_legacy[i]
      
      if (class_fund$payroll_db_new[i] == 0) {
        class_fund$amo_rate_new[i] <- 0
      } else {
        class_fund$amo_rate_new[i] <- sum(future_hire_amo_pay_table[i-1,]) / class_fund$payroll_db_new[i]
      }
      
      #Employer contribution rates (DC)
      if (class == "drop") {
        class_fund$er_dc_rate_legacy[i] <- 0
        class_fund$er_dc_rate_new[i] <- 0
      } else {
        class_fund$er_dc_rate_legacy[i] <- get(str_replace(paste0(class, "_er_dc_cont_rate_"), " ", "_"))
        class_fund$er_dc_rate_new[i] <- get(str_replace(paste0(class, "_er_dc_cont_rate_"), " ", "_"))
      }
      
      
      #Admin rate
      class_fund$admin_exp_rate[i] <- class_fund$admin_exp_rate[i-1]
      
      #Employee contribution amounts
      class_fund$ee_nc_cont_legacy[i] <- class_fund$ee_nc_rate_legacy[i] * class_fund$payroll_db_legacy[i]
      class_fund$ee_nc_cont_new[i] <- class_fund$ee_nc_rate_new[i] * (class_fund$payroll_db_new[i])
      
      frs_fund$ee_nc_cont_legacy[i] <- frs_fund$ee_nc_cont_legacy[i] + class_fund$ee_nc_cont_legacy[i]
      frs_fund$ee_nc_cont_new[i] <- frs_fund$ee_nc_cont_new[i] + class_fund$ee_nc_cont_new[i]
      
      #Admin expense amounts
      class_fund$admin_exp_legacy[i] <- class_fund$admin_exp_rate[i] * class_fund$payroll_db_legacy[i]
      class_fund$admin_exp_new[i] <- class_fund$admin_exp_rate[i] * (class_fund$payroll_db_new[i])
      
      frs_fund$admin_exp_legacy[i] <- frs_fund$admin_exp_legacy[i] + class_fund$admin_exp_legacy[i]
      frs_fund$admin_exp_new[i] <- frs_fund$admin_exp_new[i] + class_fund$admin_exp_new[i]
      
      #Employer contribution amounts (DB)
      class_fund$er_nc_cont_legacy[i] <- class_fund$er_nc_rate_legacy[i] * class_fund$payroll_db_legacy[i] + class_fund$admin_exp_legacy[i]
      class_fund$er_nc_cont_new[i] <- class_fund$er_nc_rate_new[i] * (class_fund$payroll_db_new[i]) + class_fund$admin_exp_new[i]
      
      class_fund$er_amo_cont_legacy[i] <- class_fund$amo_rate_legacy[i] * class_fund$payroll_db_legacy[i]
      class_fund$er_amo_cont_new[i] <- class_fund$amo_rate_new[i] * (class_fund$payroll_db_new[i])
      class_fund$total_er_db_cont[i] <- class_fund$er_nc_cont_legacy[i] + class_fund$er_nc_cont_new[i] + class_fund$er_amo_cont_legacy[i] + class_fund$er_amo_cont_new[i]
      
      frs_fund$er_nc_cont_legacy[i] <- frs_fund$er_nc_cont_legacy[i] + class_fund$er_nc_cont_legacy[i]
      frs_fund$er_nc_cont_new[i] <- frs_fund$er_nc_cont_new[i] + class_fund$er_nc_cont_new[i]
      
      frs_fund$er_amo_cont_legacy[i] <- frs_fund$er_amo_cont_legacy[i] + class_fund$er_amo_cont_legacy[i]
      frs_fund$er_amo_cont_new[i] <- frs_fund$er_amo_cont_new[i] + class_fund$er_amo_cont_new[i]
      frs_fund$total_er_db_cont[i] <- frs_fund$total_er_db_cont[i] + class_fund$total_er_db_cont[i]
      
      #Employer contribution amounts (DC)
      class_fund$er_dc_cont_legacy[i] <- class_fund$er_dc_rate_legacy[i] * class_fund$payroll_dc_legacy[i]
      class_fund$er_dc_cont_new[i] <- class_fund$er_dc_rate_new[i] * class_fund$payroll_dc_new[i]
      class_fund$total_er_dc_cont[i] <- class_fund$er_dc_cont_legacy[i] + class_fund$er_dc_cont_new[i]
      
      frs_fund$er_dc_cont_legacy[i] <- frs_fund$er_dc_cont_legacy[i] + class_fund$er_dc_cont_legacy[i]
      frs_fund$er_dc_cont_new[i] <- frs_fund$er_dc_cont_new[i] + class_fund$er_dc_cont_new[i]
      frs_fund$total_er_dc_cont[i] <- frs_fund$total_er_dc_cont[i] + class_fund$total_er_dc_cont[i]
      
      #Simulated returns
      class_fund$roa[i] <- return_scenarios[which(return_scenarios$year == class_fund$year[i]), return_scen_index][[1]]
      frs_fund$roa[i] <- return_scenarios[which(return_scenarios$year == class_fund$year[i]), return_scen_index][[1]]
      
      #Solvency contribution and cash flows
      cf_legacy <- class_fund$ee_nc_cont_legacy[i] + class_fund$er_nc_cont_legacy[i] + class_fund$er_amo_cont_legacy[i] - class_fund$ben_payment_legacy[i] - class_fund$refund_legacy[i] - class_fund$admin_exp_legacy[i]
      cf_new <- class_fund$ee_nc_cont_new[i] + class_fund$er_nc_cont_new[i] + class_fund$er_amo_cont_new[i] - class_fund$ben_payment_new[i] - class_fund$refund_new[i] - class_fund$admin_exp_new[i]
      cf_total <- cf_legacy + cf_new
      
      class_fund$total_solv_cont[i] <- max(-(class_fund$mva[i-1] * (1 + class_fund$roa[i]) + cf_total * (1 + class_fund$roa[i])^0.5) / (1 + class_fund$roa[i])^0.5, 0)
      class_fund$solv_cont_legacy[i] <- class_fund$total_solv_cont[i] * class_fund$aal_legacy[i] / class_fund$total_aal[i]
      class_fund$solv_cont_new[i] <- class_fund$total_solv_cont[i] * class_fund$aal_new[i] / class_fund$total_aal[i]
      
      class_fund$net_cf_legacy[i] <- cf_legacy + class_fund$solv_cont_legacy[i]
      class_fund$net_cf_new[i] <- cf_new + class_fund$solv_cont_new[i]
      
      frs_fund$net_cf_legacy[i] <- frs_fund$net_cf_legacy[i] + class_fund$net_cf_legacy[i]
      frs_fund$net_cf_new[i] <- frs_fund$net_cf_new[i] + class_fund$net_cf_new[i]
      
      #MVA projection
      class_fund$mva_legacy[i] <- class_fund$mva_legacy[i-1] * (1 + class_fund$roa[i]) + class_fund$net_cf_legacy[i] * (1 + class_fund$roa[i])^0.5
      class_fund$mva_new[i] <- class_fund$mva_new[i-1] * (1 + class_fund$roa[i]) + class_fund$net_cf_new[i] * (1 + class_fund$roa[i])^0.5
      class_fund$total_mva[i] <- class_fund$mva_legacy[i] + class_fund$mva_new[i]
      
      frs_fund$mva_legacy[i] <- frs_fund$mva_legacy[i] + class_fund$mva_legacy[i]
      frs_fund$mva_new[i] <- frs_fund$mva_new[i] + class_fund$mva_new[i]
      frs_fund$total_mva[i] <- frs_fund$total_mva[i] + class_fund$total_mva[i]
      
      #AVA development prep
      class_fund$ava_base_legacy[i] <- class_fund$ava_legacy[i-1] + class_fund$net_cf_legacy[i]/2
      class_fund$ava_base_new[i] <- class_fund$ava_new[i-1] + class_fund$net_cf_new[i]/2
      
      #Assign the class outputs back to the funding_list
      funding_list[[class]] <- class_fund
    }
    
    #AVA legacy development (step 1: calculate FRS's AVA)
    frs_fund$exp_inv_earnings_ava_legacy[i] <- frs_fund$ava_legacy[i-1] * dr_current + frs_fund$net_cf_legacy[i] * dr_current/2
    frs_fund$exp_ava_legacy[i] <- frs_fund$ava_legacy[i-1] + frs_fund$net_cf_legacy[i] + frs_fund$exp_inv_earnings_ava_legacy[i]
    frs_fund$ava_legacy[i] <- max(min(frs_fund$exp_ava_legacy[i] + (frs_fund$mva_legacy[i] - frs_fund$exp_ava_legacy[i]) * 0.2, frs_fund$mva_legacy[i] * 1.2), frs_fund$mva_legacy[i] * 0.8)
    frs_fund$alloc_inv_earnings_ava_legacy[i] <- frs_fund$ava_legacy[i] - frs_fund$ava_legacy[i-1] - frs_fund$net_cf_legacy[i]
    frs_fund$ava_base_legacy[i] <- frs_fund$ava_legacy[i-1] + frs_fund$net_cf_legacy[i]/2
    
    #AVA new development (step 1: calculate FRS's AVA)
    frs_fund$exp_inv_earnings_ava_new[i] <- frs_fund$ava_new[i-1] * dr_new + frs_fund$net_cf_new[i] * dr_new/2
    frs_fund$exp_ava_new[i] <- frs_fund$ava_new[i-1] + frs_fund$net_cf_new[i] + frs_fund$exp_inv_earnings_ava_new[i]
    frs_fund$ava_new[i] <- max(min(frs_fund$exp_ava_new[i] + (frs_fund$mva_new[i] - frs_fund$exp_ava_new[i]) * 0.2, frs_fund$mva_new[i] * 1.2), frs_fund$mva_new[i] * 0.8)
    frs_fund$alloc_inv_earnings_ava_new[i] <- frs_fund$ava_new[i] - frs_fund$ava_new[i-1] - frs_fund$net_cf_new[i]
    frs_fund$ava_base_new[i] <- frs_fund$ava_new[i-1] + frs_fund$net_cf_new[i]/2
    
    
    for (class in class_names_no_frs) {
      #Do the assignment below to declutter the code
      class_fund <- funding_list[[class]]
      
      #AVA legacy development (step 2: calculate class's unadjusted AVA)
      class_fund$alloc_inv_earnings_ava_legacy[i] <- frs_fund$alloc_inv_earnings_ava_legacy[i] * class_fund$ava_base_legacy[i]/frs_fund$ava_base_legacy[i]
      class_fund$unadj_ava_legacy[i] <- class_fund$ava_legacy[i-1] + class_fund$net_cf_legacy[i] + class_fund$alloc_inv_earnings_ava_legacy[i]
      
      #AVA new development (step 2: calculate class's unadjusted AVA)
      class_fund$alloc_inv_earnings_ava_new[i] <- if_else(frs_fund$ava_base_new[i] == 0, 0, frs_fund$alloc_inv_earnings_ava_new[i] * class_fund$ava_base_new[i]/frs_fund$ava_base_new[i])
      class_fund$unadj_ava_new[i] <- class_fund$ava_new[i-1] + class_fund$net_cf_new[i] + class_fund$alloc_inv_earnings_ava_new[i]
      
      #Assign the class outputs back to the funding_list
      funding_list[[class]] <- class_fund
    }
    
    #DROP asset reallocation
    drop_fund <- funding_list$drop
    
    drop_fund$net_reallocation_legacy[i] <- drop_fund$unadj_ava_legacy[i] - drop_fund$aal_legacy[i] * frs_fund$ava_legacy[i] / frs_fund$aal_legacy[i]
    drop_fund$ava_legacy[i] <- drop_fund$unadj_ava_legacy[i] - drop_fund$net_reallocation_legacy[i]
    
    drop_fund$net_reallocation_new[i] <- if_else(frs_fund$aal_new[i] == 0, 0, drop_fund$unadj_ava_new[i] - drop_fund$aal_new[i] * frs_fund$ava_new[i] / frs_fund$aal_new[i])
    drop_fund$ava_new[i] <- drop_fund$unadj_ava_new[i] - drop_fund$net_reallocation_new[i]
    
    #Assign the DROP's updated numbers back to the funding_list
    funding_list$drop <- drop_fund
    
    for (class in class_names_no_drop_frs) {
      #Do the assignment below to declutter the code
      class_fund <- funding_list[[class]]
      
      #AVA legacy development (step 3: calculate class's adjusted AVA)
      class_drop_prop_legacy <- class_fund$aal_legacy[i] / (frs_fund$aal_legacy[i] - funding_list$drop$aal_legacy[i])
      class_fund$net_reallocation_legacy[i] <- class_drop_prop_legacy * funding_list$drop$net_reallocation_legacy[i]
      class_fund$ava_legacy[i] <- class_fund$unadj_ava_legacy[i] + class_fund$net_reallocation_legacy[i]
      
      #AVA new development (step 3: calculate class's adjusted AVA)
      class_drop_prop_new <- if_else((frs_fund$aal_new[i] - funding_list$drop$aal_new[i]) == 0, 0, class_fund$aal_new[i] / (frs_fund$aal_new[i] - funding_list$drop$aal_new[i]))
      class_fund$net_reallocation_new[i] <- class_drop_prop_new * funding_list$drop$net_reallocation_new[i]
      class_fund$ava_new[i] <- class_fund$unadj_ava_new[i] + class_fund$net_reallocation_new[i]
      
      #Assign the class outputs back to the funding_list
      funding_list[[class]] <- class_fund
    }
    
    ####AVA, UAL, funded ratio projections, and all-in-cost
    for (class in class_names_no_frs) {
      #Do the assignment below to declutter the code
      class_fund <- funding_list[[class]]
      
      class_fund$total_ava[i] <- class_fund$ava_legacy[i] + class_fund$ava_new[i]
      
      frs_fund$total_ava[i] <- frs_fund$total_ava[i] + class_fund$total_ava[i]
      
      class_fund$ual_ava_legacy[i] <- class_fund$aal_legacy[i] - class_fund$ava_legacy[i]
      class_fund$ual_ava_new[i] <- class_fund$aal_new[i] - class_fund$ava_new[i]
      class_fund$total_ual_ava[i] <- class_fund$ual_ava_legacy[i] + class_fund$ual_ava_new[i]
      
      frs_fund$ual_ava_legacy[i] <- frs_fund$ual_ava_legacy[i] + class_fund$ual_ava_legacy[i]
      frs_fund$ual_ava_new[i] <- frs_fund$ual_ava_new[i] + class_fund$ual_ava_new[i]
      frs_fund$total_ual_ava[i] <- frs_fund$total_ual_ava[i] + class_fund$total_ual_ava[i]
      
      class_fund$ual_mva_legacy[i] <- class_fund$aal_legacy[i] - class_fund$mva_legacy[i]
      class_fund$ual_mva_new[i] <- class_fund$aal_new[i] - class_fund$mva_new[i]
      class_fund$total_ual_mva[i] <- class_fund$ual_mva_legacy[i] + class_fund$ual_mva_new[i]
      
      frs_fund$ual_mva_legacy[i] <- frs_fund$ual_mva_legacy[i] + class_fund$ual_mva_legacy[i]
      frs_fund$ual_mva_new[i] <- frs_fund$ual_mva_new[i] + class_fund$ual_mva_new[i]
      frs_fund$total_ual_mva[i] <- frs_fund$total_ual_mva[i] + class_fund$total_ual_mva[i]
      
      class_fund$fr_mva[i] <- class_fund$total_mva[i] / class_fund$total_aal[i]
      class_fund$fr_ava[i] <- class_fund$total_ava[i] / class_fund$total_aal[i]
      
      frs_fund$fr_mva[i] <- frs_fund$total_mva[i] / frs_fund$total_aal[i]
      frs_fund$fr_ava[i] <- frs_fund$total_ava[i] / frs_fund$total_aal[i]
      
      #Contribution analysis
      class_fund$total_er_cont[i] <- class_fund$total_er_db_cont[i] + class_fund$total_er_dc_cont[i] + class_fund$total_solv_cont[i]
      frs_fund$total_er_cont[i] <- frs_fund$total_er_cont[i] + class_fund$total_er_cont[i]
      
      class_fund$total_er_cont_rate[i] <- class_fund$total_er_cont[i] / class_fund$total_payroll[i]
      frs_fund$total_er_cont_rate[i] <- frs_fund$total_er_cont[i] / frs_fund$total_payroll[i]
    
      #All-in-cost analysis
      class_fund$total_er_cont_real[i] <- class_fund$total_er_cont[i] / (1 + inflation_)^(class_fund$year[i] - start_year_)
      frs_fund$total_er_cont_real[i] <- frs_fund$total_er_cont_real[i] + class_fund$total_er_cont_real[i]
      
      if (i == 2) {
        class_fund$cum_er_cont_real[i] <- class_fund$total_er_cont_real[i]
      } else {
        class_fund$cum_er_cont_real[i] <- class_fund$cum_er_cont_real[i - 1] + class_fund$total_er_cont_real[i]  
      }
      
      frs_fund$cum_er_cont_real[i] <- frs_fund$cum_er_cont_real[i] + class_fund$cum_er_cont_real[i]
      
      class_fund$total_ual_mva_real[i] <- class_fund$total_ual_mva[i] / (1 + inflation_)^(class_fund$year[i] - start_year_)
      frs_fund$total_ual_mva_real[i] <- frs_fund$total_ual_mva_real[i] + class_fund$total_ual_mva_real[i]
      
      class_fund$all_in_cost_real[i] <- class_fund$cum_er_cont_real[i] + class_fund$total_ual_mva_real[i]
      frs_fund$all_in_cost_real[i] <- frs_fund$all_in_cost_real[i] + class_fund$all_in_cost_real[i]
      
      
      #Assign the class outputs back to the funding_list
      funding_list[[class]] <- class_fund
    }
    
    ####Amortization calculations
    for (class in class_names_no_frs) {
      #Do the assignment below to declutter the code
      class_fund <- funding_list[[class]]
      
      current_hire_debt_layer_table <- current_hire_debt_layer_list[[class]]
      future_hire_debt_layer_table <- future_hire_debt_layer_list[[class]]
      
      current_hire_amo_period_table <- current_hire_amo_period_list[[class]]
      future_hire_amo_period_table <- future_hire_amo_period_list[[class]]
      
      current_hire_amo_pay_table <- current_hire_amo_payment_list[[class]]
      future_hire_amo_pay_table <- future_hire_amo_payment_list[[class]]
      
      #Amortization for legacy hires
      current_hire_debt_layer_table[i, 2:ncol(current_hire_debt_layer_table)] <- current_hire_debt_layer_table[i-1, 1:(ncol(current_hire_debt_layer_table)-1)] * (1 + dr_current) - current_hire_amo_pay_table[i-1, 1:ncol(current_hire_amo_pay_table)] * (1 + dr_current)^0.5
      current_hire_debt_layer_table[i, 1] <- class_fund$ual_ava_legacy[i] - sum(current_hire_debt_layer_table[i, 2:ncol(current_hire_debt_layer_table)])
      
      current_hire_amo_pay_table[i, 1:ncol(current_hire_amo_pay_table)] <- get_pmt(r = dr_current,
                                                                                   g = amo_pay_growth,
                                                                                   nper = current_hire_amo_period_table[i, 1:ncol(current_hire_amo_period_table)],
                                                                                   pv = current_hire_debt_layer_table[i, 1:(ncol(current_hire_debt_layer_table)-1)],
                                                                                   t = 0.5)
      
      #Amortization for future hires
      future_hire_debt_layer_table[i, 2:ncol(future_hire_debt_layer_table)] <- future_hire_debt_layer_table[i-1, 1:(ncol(future_hire_debt_layer_table)-1)] * (1 + dr_new) - future_hire_amo_pay_table[i-1, 1:ncol(future_hire_amo_pay_table)] * (1 + dr_new)^0.5
      future_hire_debt_layer_table[i, 1] <- class_fund$ual_ava_new[i] - sum(future_hire_debt_layer_table[i, 2:ncol(future_hire_debt_layer_table)])
      
      future_hire_amo_pay_table[i, 1:ncol(future_hire_amo_pay_table)] <- get_pmt(r = dr_new,
                                                                                 g = amo_pay_growth,
                                                                                 nper = future_hire_amo_period_table[i, 1:ncol(future_hire_amo_period_table)],
                                                                                 pv = future_hire_debt_layer_table[i, 1:(ncol(future_hire_debt_layer_table)-1)],
                                                                                 t = 0.5)
      
      #Assign the amortization outputs back to respective tables
      current_hire_debt_layer_list[[class]] <- current_hire_debt_layer_table
      future_hire_debt_layer_list[[class]] <- future_hire_debt_layer_table
      
      current_hire_amo_payment_list[[class]] <- current_hire_amo_pay_table
      future_hire_amo_payment_list[[class]] <- future_hire_amo_pay_table
    }
    
    
  
    #Assign the FRS's updated numbers back to the funding_list
    funding_list$frs <- frs_fund
    
  }
  
  output <- funding_list
  
  return(output)
  
}  
# write.csv(output, "output.csv")  
#   return(output)
#   
# }