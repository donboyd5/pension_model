resetEnvironment <- function() {
  graphics.off()  # Close all graphics devices
  rm(list = ls(all.names = TRUE))  # Remove all objects
  lapply(search(), function(x) {
    if (grepl("package:", x)) {
      detach(x, unload = TRUE, character.only = TRUE)
    }
  })
  gc()  # Explicit garbage collection
}