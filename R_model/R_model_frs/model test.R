source("Florida FRS master.R")


regular_benefit_check <- get_benefit_data("regular")
special_benefit_check <- get_benefit_data("special")
admin_benefit_check <- get_benefit_data("admin")
eco_benefit_check <- get_benefit_data("eco")
eso_benefit_check <- get_benefit_data("eso")
judges_benefit_check <- get_benefit_data("judges")
senior_management_benefit_check <- get_benefit_data("senior_management")


0.0896 / regular_benefit_check$agg_norm_cost_table
0.2013 / special_benefit_check$agg_norm_cost_table
0.1457 / admin_benefit_check$agg_norm_cost_table
0.1254 / eco_benefit_check$agg_norm_cost_table
0.1463 / eso_benefit_check$agg_norm_cost_table
0.1777 / judges_benefit_check$agg_norm_cost_table
0.1086 / senior_management_benefit_check$agg_norm_cost_table


regular_salary <- regular_benefit_check$benefit_val_table %>%
  select(entry_year, entry_age, term_age, salary)


check <- regular_salary_headcount_table %>%
  left_join(regular_salary, by = c("entry_year", "entry_age", "age" = "term_age")) %>%
  summarise(payroll = sum(salary * count, na.rm = T))

check$payroll / 29126383663


regular_liability_check <- get_liability_data("regular")
special_liability_check <- get_liability_data("special")
admin_liability_check <- get_liability_data("admin")
eco_liability_check <- get_liability_data("eco")
eso_liability_check <- get_liability_data("eso")
judges_liability_check <- get_liability_data("judges")
senior_management_liability_check <- get_liability_data("senior_management")


(regular_liability_check$payroll_db_est / regular_liability_check$payroll_est) * 29126383663  





 
#get the payroll numbers across classes from the liability outputs

liability_list <- list(regular_liability_check = regular_liability_check,
                       special_liability_check = special_liability_check,
                       admin_liability_check = admin_liability_check,
                       eco_liability_check = eco_liability_check,
                       eso_liability_check = eso_liability_check,
                       judges_liability_check = judges_liability_check,
                       senior_management_liability_check = senior_management_liability_check)

#create empty frs_liability table with the same structure as the liability tables
frs_liability <- data.frame(matrix(0, ncol = ncol(regular_liability_check), nrow = nrow(regular_liability_check)))
colnames(frs_liability) <- colnames(regular_liability_check)

#sum all the data in the liability tables except for the year column and any column with "rate" in the name
for (liability_table in liability_list) {
  liability_table <- liability_table[-which(names(liability_table) == "year" | str_detect(names(liability_table), "rate"))]
  frs_liability[-which(names(frs_liability) == "year" | str_detect(names(frs_liability), "rate"))] <- frs_liability[-which(names(frs_liability) == "year" | str_detect(names(frs_liability), "rate"))] + liability_table
}




