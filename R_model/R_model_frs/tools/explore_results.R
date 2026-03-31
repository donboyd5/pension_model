


# INFORMATAIONAL ONLY ------
# prepare comparisons of new vs. Reason -----------------------------------

# load each result into its own environment
# oldpath <- here::here("reason_results", "reason_workspace.RData")
# newpath <- here::here("new_results", "new_workspace.RData")

# load(oldpath, oldws <- new.env())
# load(newpath, newws <- new.env())

# get names of objects in each workspace
# oldnames <- ls(name=oldws) # names of objects in the workspace
# oldnames # almost 300 objects!; already sorted by name

# newnames <- ls(name=newws) # names of objects in the workspace
# newnames # almost 300 objects!; already sorted by name

# get(objnames[119], envir=rws) # how to get an object from the workspace



# get baseline_funding list old and new --------------------------------

# blfunding_old <- get("baseline_funding", envir=oldws)
# blfunding_new <- get("baseline_funding", envir=newws)

# names(blfunding_old)
# names(blfunding_new)

# stack the two sets of data frames so they can be compared ----
#. first, fix the names to remove spaces ----
# fixnames <- function(list){
#   names(list)[names(list) == "senior management"] <- "senior_management"
#   return(list)
# }

# blfunding_old <- fixnames(blfunding_old)
# blfunding_new <- fixnames(blfunding_new)

# names(blfunding_old)
# names(blfunding_new)

#. stack the data frames ----

# str(blfunding_old)

# olddf <- bind_rows(blfunding_old, .id = "class") |> 
#   pivot_longer(-c(class, year),
#                values_to = "value")

# newdf <- bind_rows(blfunding_old, .id = "class") |> 
#   pivot_longer(-c(class, year),
#                values_to = "value")

# all.equal(olddf, newdf)

# comp <- left_join(olddf, newdf,
#                   by = join_by(class, year, name))



