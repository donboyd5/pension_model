

mva <- c(1,NA,NA,NA)
cont <- c(1,3,6,5)
aal <- c(3,7,15,21)
unadj_fr <- c(1/3, NA, NA, NA)
fr <- c(1/3, NA, NA, NA)
reallocation <- c(0,0,0,0)

x <- data.frame(mva, cont, aal, unadj_fr, fr, reallocation)



mva <- c(1,NA,NA,NA)
cont <- c(1,4,6,8)
aal <- c(3,7,15,25)
unadj_fr <- c(1/3, NA, NA, NA)
fr <- c(1/3, NA, NA, NA)
reallocation <- c(0,0,0,0)

y <- data.frame(mva, cont, aal, unadj_fr, fr, reallocation)


mva <- c(1,NA,NA,NA)
cont <- c(1,10,4,4)
aal <- c(3,6,10,20)
unadj_fr <- c(1/3, NA, NA, NA)
fr <- c(1/3, NA, NA, NA)
reallocation <- c(0,0,0,0)


z <- data.frame(mva, cont, aal, unadj_fr, fr, reallocation)



frs <- x + y + z
frs <- frs %>% 
  mutate(unadj_fr = mva / aal,
         fr = mva / aal,
         cont = if_else(row_number() == 1, cont, 0),
         aal = if_else(row_number() == 1, aal, 0))

frs[is.na(frs)] <- 0


list_names <- c("x", "y", "z", "frs")

my_list <- mget(list_names)

list_names_no_frs <- names(my_list)[-which(names(my_list) == "frs")]

for (i in 2:nrow(my_list[[1]])) {
  frs_data <- my_list$frs
  for (list in list_names_no_frs) {
    data <- my_list[[list]]
    
    data$mva[i] <- data$mva[i-1] + data$cont[i]
    data$unadj_fr[i] <- data$mva[i] / data$aal[i]
    my_list[[list]] <- data
    
    frs_data$mva[i] <- frs_data$mva[i] + data$mva[i]
    frs_data$cont[i] <- frs_data$cont[i] + data$cont[i]
    frs_data$aal[i] <- frs_data$aal[i] + data$aal[i]
    
    
  } 
  frs_data$unadj_fr[i] <- frs_data$mva[i] / frs_data$aal[i]
  frs_data$fr[i] <- frs_data$unadj_fr[i]
  
  total_reallocation <- my_list$z$mva[i] - my_list$z$aal[i] * frs_data$fr[i]
  
  for (list in list_names_no_frs) {
    data <- my_list[[list]]
    aal_proportion <- data$aal[i] / (frs_data$aal[i] - my_list$z$aal[i])
    if (list == "z") {
      data$reallocation[i] <- total_reallocation
      data$mva[i] <- data$mva[i] - data$reallocation[i]
    } else {
      data$reallocation[i] <- total_reallocation * aal_proportion
      data$mva[i] <- data$mva[i] + data$reallocation[i]
    }
    data$fr[i] <- data$mva[i] / data$aal[i]
    my_list[[list]] <- data
  }
  
  my_list$frs <- frs_data
  
}

export(my_list, file = "my_list.xlsx")

my_list[[1]]





