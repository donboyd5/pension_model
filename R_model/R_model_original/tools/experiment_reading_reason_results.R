source(here::here("tools", "libraries.R")) # load all tools
source(here::here("tools", "functions.R"))

# TEST reading the workspace ----------------------------------------------
# load Reason FRS workspace into its OWN environment I call rws

# load takes some time
wspath <- here::here("reason_results", "reason_workspace.RData")

load(wspath, rws <- new.env())

objnames <- ls(name=rws) # names of objects in the workspace
objnames # almost 300 objects!; already sorted by name

get(objnames[119], envir=rws) # how to get an object from the workspace


# EXAMPLE code for getting the workforce data frames and stacking them into generalizable data frames --------------------

#. prepare class names and dataframe names ---------------------------------

# Reason used seniormanagement as a class name
#  but used senior_management in dataframe names

reason_classes <- c("regular", "special", "admin", "eco", "eso", "judges", "seniormanagement")

wfclasses <- reason_classes |>
  str_replace("seniormanagement", "senior_management")

wfnames <- paste0(wfclasses, "_wf_data")
wfnames # names of wf objects to extract from Reason workspace

cbind(wfclasses, wfnames) # make sure they look right


#. unpack the data -------

# get one big list of lists of data frames
# outer list has 7 lists, one for each class
# each inner list has 4 data frames
#   wf_active_df, term, refund, retire
# they are similar but not the same in structure, but the same structure for each class

wflist <- wfnames |>
  purrr::map(\(x) get(x, envir=rws))|>
  purrr::set_names(wfclasses)

names(wflist)
(wfdfnames <- names(wflist[[1]])) # names of the 4 data frames for each class

# get 4 data frames, with classes stacked
nested <- wflist |>
  as_tibble() |>
  mutate(dfname=wfdfnames) |>
  pivot_longer(cols = -dfname, names_to = "class") |>
  pivot_wider(names_from = dfname)
# note that wf_retire_df is a dt data.table, others are df data.frame

# if needed we can convert with:
# nested |>
#   mutate(wf_retire_df = map(wf_retire_df, as.data.frame))

unpack_dframes <- function(colname){
  # for a single data frame name (colname), stack all 7 classes into a single data frame
  # and put the stacked data frame into the environment
  print(colname)
  df <- nested |>
    select(class, nestcol=all_of(colname)) |>
    unnest_wider(col=nestcol) |>
    unnest_longer(col=-class)
  assign(colname, df, envir = .GlobalEnv)
}

purrr::walk(wfdfnames, unpack_dframes)  # unpack and stack all classes for each of the 4 data frames
