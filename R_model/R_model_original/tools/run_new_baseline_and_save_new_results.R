
# run the following in a CLEAN environment with the branch of interest checked out --------------------------------

# RESET ENVIRONMENT MANUALLY !!!!!  

# Ctrl-Shift-F10 to restart RStudio and clear the environment


source(here::here("Florida FRS master.R")) # load and run the full FRS Florida model

# generate baseline results
baseline_funding <- get_funding_data()
baseline_liability <- get_liability_data()

save.image(here::here("new_results", "new_workspace.RData")) # save the entire workspace

source(here::here("run_tests.R")) # run tests

