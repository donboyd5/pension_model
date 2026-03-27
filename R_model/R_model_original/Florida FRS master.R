rm(list = ls())

#Loading required libraries
library("readxl")
library(tidyverse)
library(zoo)
library(profvis)
library(data.table)
library(openxlsx)
library(janitor)
library(rio)
library(parallel)

#Get actuarial and financial functions
source("utility_functions.R")

#Get model inputs and assumptions
source("Florida FRS model input.R")

#Get benefit data and model
source("Florida FRS benefit model.R")

#Get workforce data (run this model only when workforce data is updated, otherwise use the rds files)
source("Florida FRS workforce model.R")
get_wf_data(class_name = "regular")
get_wf_data(class_name = "special")
get_wf_data(class_name = "admin")
get_wf_data(class_name = "eco")
get_wf_data(class_name = "eso")
get_wf_data(class_name = "judges")
get_wf_data(class_name = "senior management")


#Get liability model
regular_wf_data <- readRDS("regular_wf_data.rds")
special_wf_data <- readRDS("special_wf_data.rds")
admin_wf_data <- readRDS("admin_wf_data.rds")
eco_wf_data <- readRDS("eco_wf_data.rds")
eso_wf_data <- readRDS("eso_wf_data.rds")
judges_wf_data <- readRDS("judges_wf_data.rds")
senior_management_wf_data <- readRDS("senior_management_wf_data.rds")
source("Florida FRS liability model.R")


#Get funding model
source("Florida FRS funding model.R")

##############################################TESTING############################################

# baseline_funding <- get_funding_data()
# 
# funding_72return <- get_funding_data(return_scen = "model",
#                                      model_return = 0.072)
# 
# funding_62return <- get_funding_data(return_scen = "model",
#                                      model_return = 0.062)
# 
# 
# check_72 <- funding_72return$frs %>% 
#   select(year, total_ual_mva, total_ual_ava, fr_mva, fr_ava)
# 
# 
# check_62 <- funding_62return$frs %>% 
#   select(year, total_ual_mva, total_ual_ava, fr_mva, fr_ava)
# 
# 
# export(baseline_funding, "baseline_funding.xlsx")
# 
# 
# baseline_liability <- get_liability_data()
# 
# cola1_constant_liability <- get_liability_data(cola_tier_1_active_constant = "yes")

# baseline_liability <- get_liability_data()
# baseline <- get_funding_data()
# 
# lower_amo <- get_funding_data(funding_policy = "ADC",
#                               amo_period_current = 23,
#                               amo_period_new = 23)
# 
# 
# anthony_scen2 <- get_funding_data(cola_current_active = 0.0071,
#                                  cola_new_active = 0.0071,
#                                  cola_current_retire = 0.0071,
#                                  funding_policy = "ADC",
#                                  amo_period_current = 50,
#                                  amo_period_new = 15,
#                                  dr_new = 0.06)
# 
# 
# anthony_scen_liab2 <- get_liability_data(cola_current_active = 0.0071,
#                                         cola_new_active = 0.0071,
#                                         cola_current_retire = 0.0071,
#                                         dr_new = 0.06)
# 
# write.csv(lower_amo, "lower_amo.csv")
# test_nc <- get_benefit_data(retire_refund_ratio = 0.3)
# 
# test_nc$nc_agg$normal_cost_aggregate_DB
# 
# test_liability <- get_liability_data(retire_refund_ratio = 0.3,
#                                      cal_factor = 10.6/12.9)
# 
# baseline <- get_liability_data()
# lower_dr_new <- get_liability_data(dr_new = 0.06)
# lower_dr <- get_liability_data(dr_new = 0.06, dr_current = 0.06)
# cola_everyone <- get_liability_data(cola_current_active = 0.03,
#                                     cola_new_active = 0.03,
#                                     cola_current_retire = 0.03)
# 
# cola_one <- get_liability_data(one_time_cola = T, cola_current_retire_one = 0.03, cal_factor = 10.8 / 13)
