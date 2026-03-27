source(here::here("tools", "libraries.R")) # load all tools
source(here::here("tools", "functions.R"))

fun <- get_salary_headcount_table
fun <- get_tier


codetools::checkUsage(fun)

codetools::findGlobals(fun, merge = FALSE)
