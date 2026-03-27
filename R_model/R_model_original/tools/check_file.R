
source(here::here("tools", "libraries.R")) # load all tools
source(here::here("tools", "functions.R"))

filename <- "utility_functions.R"
filename <- "Florida FRS model input.R"
filename <- "Florida FRS benefit model.R"
filename <- "abc.R"



# linting -----------------------------------------------------------------


lint(here::here(filename))


# check for live code -----------------------------------------------------


pre_objects <- sapply(ls(), function(x) class(get(x))) # Capture existing objects and their classes

# source("utility_functions.R")
source(here::here(filename))

post_objects <- sapply(ls(), function(x) class(get(x)))

# Identify new objects
new_objects <- setdiff(names(post_objects), names(pre_objects))
if (length(new_objects) > 0) {
  cat("New objects added:\n", paste(new_objects, collapse=", "), "\n")
} else {
  cat("No new objects added.\n")
}

# Identify removed objects
removed_objects <- setdiff(names(pre_objects), names(post_objects))
if (length(removed_objects) > 0) {
  cat("Objects removed:\n", paste(removed_objects, collapse=", "), "\n")
} else {
  cat("No objects removed.\n")
}

# Identify changed objects (optional)
# This checks if any object's class has changed
changed_objects <- names(Filter(function(x) pre_objects[x] != post_objects[x], intersect(names(pre_objects), names(post_objects))))
if (length(changed_objects) > 0) {
  cat("Objects changed:\n", paste(changed_objects, collapse=", "), "\n")
} else {
  cat("No objects changed.\n")
}


# Assuming 'pre_objects' and 'post_objects' are already defined from previous steps

# Identify new objects
new_objects <- setdiff(names(post_objects), names(pre_objects))

# Filter new objects to find non-functions
non_function_new_objects <- sapply(new_objects, function(x) {
  obj <- get(x)
  # Check if object is not a function
  if (!inherits(obj, "function")) {
    return(class(obj))
  } else {
    return(NULL)  # Return NULL for functions
  }
})

# Clean up the list to remove NULL entries
non_function_new_objects <- non_function_new_objects[!sapply(non_function_new_objects, is.null)]

# Display non-function objects
if (length(non_function_new_objects) > 0) {
  cat("New non-function objects added:\n")
  print(non_function_new_objects)
} else {
  cat("No new non-function objects added.\n")
}








