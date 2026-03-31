
# run the following in a CLEAN environment --------------------------------

# To recreate Reason results, checkout main branch and run the code.
# This code may not be in the main branch, in which case you'll have to make it available.

# run the full FRS Florida model

source(here::here("Florida FRS master.R")) # load the model

# generate baseline results

baseline_funding <- get_funding_data()
baseline_liability <- get_liability_data()

# save the entire workspace
save.image(here::here("reason_results", "reason_workspace.RData"))

#   workspace was saved on 8/11/2024 and again on 8/12/2024 (I lost the 8/11/2024 copy)
