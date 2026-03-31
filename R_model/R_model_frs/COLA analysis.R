#COLA analysis

source("Florida FRS master.R")

#baseline policy with constant 6.7% return
baseline_funding_67return <- get_funding_data()

#baseline policy with 2 recessions scenario
baseline_funding_2recession <- get_funding_data(return_scen = "recur_recession")

#COLA policy with constant 6.7% return
cola_funding_67return <- get_funding_data(cola_tier_1_active_constant = "yes",
                                          cola_tier_1_active = 0.03,
                                          cola_tier_2_active = 0.03,
                                          cola_tier_3_active = 0.03)

#COLA policy with 2 recessions scenario
cola_funding_2recession <- get_funding_data(cola_tier_1_active_constant = "yes",
                                            cola_tier_1_active = 0.03,
                                            cola_tier_2_active = 0.03,
                                            cola_tier_3_active = 0.03,
                                            return_scen = "recur_recession")


target_col <- c("year", "roa", "total_mva", "total_aal", "total_ual_mva", "total_ual_ava", "fr_mva", "fr_ava", "total_er_cont_rate", "total_er_cont_real", "cum_er_cont_real",	"total_ual_mva_real",	"all_in_cost_real")

baseline_funding_67return_short <- baseline_funding_67return$frs %>% 
  select(any_of(target_col)) %>% 
  mutate(across(!c(year, roa, fr_mva, fr_ava, total_er_cont_rate), ~ .x / 1000000000))

baseline_funding_2recession_short <- baseline_funding_2recession$frs %>%
  select(any_of(target_col)) %>% 
  mutate(across(!c(year, roa, fr_mva, fr_ava, total_er_cont_rate), ~ .x / 1000000000))

cola_funding_67return_short <- cola_funding_67return$frs %>%
  select(any_of(target_col)) %>% 
  mutate(across(!c(year, roa, fr_mva, fr_ava, total_er_cont_rate), ~ .x / 1000000000))

cola_funding_2recession_short <- cola_funding_2recession$frs %>%
  select(any_of(target_col)) %>% 
  mutate(across(!c(year, roa, fr_mva, fr_ava, total_er_cont_rate), ~ .x / 1000000000))


output_list <- list(baseline_funding_67 = baseline_funding_67return_short,
                    baseline_funding_2recession = baseline_funding_2recession_short,
                    cola_funding_67 = cola_funding_67return_short,
                    cola_funding_2recession = cola_funding_2recession_short)


export(output_list, "output_list.xlsx")

