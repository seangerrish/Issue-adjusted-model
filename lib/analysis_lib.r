library(ggplot2)
library(plyr)

OFFSET.COLUMNS <- paste("Offset", 0:73, sep="")

NUMBER.TOPICS <- 74
E.THETA.COLUMNS <- paste("Etheta", 1:NUMBER.TOPICS, sep=".")
GAMMA.COLUMNS = paste("Gamma", 1:NUMBER.TOPICS, sep=".")

TOPICS <- read.csv("../3240/topics_labeled_two_iterations.csv",
                   as.is=TRUE)

read.billtitles <- function() {
  bill.titles <- read.csv("/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2.billtitles.csv",
                          as.is=TRUE,
                          header=FALSE,
                          col.names=c("DocId",
                            "Session",
                            "BillNumber",
                            "BillChamber",
                            "Title"))
}

read.gammas <- function() {
  gammas <- read.csv("/n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma",
                     as.is=TRUE,
                     sep=" ",
                     header=FALSE,
                     col.names=GAMMA.COLUMNS)

  doc.ids.mult <- scan("/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-train-mult.dat_all",
                       sep="\n", what="character")
  names(gammas)[1:ncol(gammas)] = GAMMA.COLUMNS
  doc.ids = unlist(lapply(doc.ids.mult, FUN=get.doc.ids))
  gammas$DocId = doc.ids
  gammas[, E.THETA.COLUMNS] <- gammas[, GAMMA.COLUMNS] / rowSums(gammas[, GAMMA.COLUMNS])
  gammas
}

# Define globally-useful variables.
get.doc.ids <- function(x) {
  p = strsplit(x, " ")[[1]][1]
  p
}

accuracy <- function(x, jackman=FALSE) {
  accuracy = NULL
  if (jackman) {
    accuracy <- sum((x$Prediction.Jackman > 0.5) == (x$Vote == "+")) / nrow(x)
  } else {
    x$log.odds = x$Prediction
    accuracy <- sum((x$log.odds > 0.0) == (x$Vote == "+")) / nrow(x)
  }
  baseline <- sum(x$Vote == "+") / nrow(x)
  data.frame(Accuracy=accuracy,
             Baseline=baseline,
             Count=nrow(x))
}

log.odds <- function(x) {
  user.stats <- unlist(x[, OFFSET.COLUMNS])
  e.thetas <- unlist(x[, E.THETA.COLUMNS])
  l.o <- (
          x$Popularity
          + x$Polarity * x$Ip0
          + x$Polarity *
          sum(e.thetas * (user.stats
                          + global.vector$GlobalMean *
                          x$Ip0)))
  l.o
}
 
logistic <- function(x) {
  t = exp(x) / (1 + exp(x))
  t[x > 20] = 1
  t[x < -20] = 0
  t
}

## Example usage:
## ideal.data <- ReadDataset(1.0,
##                           "s",
##                           111,
##                           "ideal",
##                           version="final")
## globalzero.data <- ReadDataset(1.0,
##                           "s",
##                           111,
##                           "globalzero",
##                           version="final")
ReadDataset <- function(weight, chamber, session, model, version="final", subset="all", issue="") { 
  # First, read all information from the variational fit of the model.
  s1 = model
  if (model == "globalzero") {
    s1 = "variational_globalzero"
  }
  if (model == "ideal") {
    s1 = "variational_ideal"
  }
  root <- "/n/fs/topics/users/sgerrish/data/legis/experiments/v12.2"

  if (class(session) == "numeric") {
    session = as.character(session)
  }
  
  print(subset)
  file.with.type.pattern <- function(weight,
                                     chamber,
                                     session,
                                     model,
                                     version="final",
                                     subset="all") {
    weight.str = sprintf("%.1f", weight)
    if (abs(weight - 0.01) < 1e-5) {
      weight.str = "0.01"
    }
    if (abs(weight - 0.001) < 1e-5) {
      weight.str = "0.001"
    }
    if (abs(weight - 0.0001) < 1e-5) {
      weight.str = "0.0001"
    }
    if (model != "globalzero" && model != "ideal" && weight == 10) {
      weight.str = "10"
    }
    if (model != "globalzero" && model != "ideal" && weight == 1 && chamber == "s") {
      weight.str = "1"
    }
    digits = max(as.integer(-log(weight)/log(10) + 0.001), 2)
    filepattern <- sprintf(
      "%%s/v12.2.ip_with_topic_discrepancies_offset_python_labeled_topics_%%s/%%s/%%s/%%s%%s.%%%%s_stats_Top74_IpDim1_weight%%.%df_subset%%s_session_%%s_chamber%%s.csv",
                           digits)
    print(subset)
    filepattern <- sprintf(
      filepattern,                           
      root,
      s1,
      session,
      weight.str,
      issue,
      version,
      weight,
      subset,
      session,
      chamber)
   print(filepattern)
    filepattern
  }
  print(subset)
  filepattern <- file.with.type.pattern(weight, chamber, session, model, version=version, subset=subset)
  
  filename <- sprintf(filepattern, "votes")
  votes <- read.csv(filename, as.is=TRUE)

  filename <- sprintf(filepattern, "lawmaker")
  lawmaker.ips <- read.csv(filename, as.is=TRUE)

  filename <- sprintf(filepattern, "docs")
  doc.stats <- read.csv(filename, as.is=TRUE,
                        col.names=c("DocId", "Polarity",
                          "Popularity", "PolarityVariance",
                          "PopularityVariance"))

  filename <- sprintf(filepattern, "global")
  global.vector <- read.csv(filename, as.is=TRUE)
  write.table(global.vector[, 1], file="tmp.csv", quote=FALSE, row.names=FALSE, col.names=FALSE)
  col.names <- names(global.vector)
  global.vector <- read.csv("tmp.csv", as.is=TRUE, header=FALSE, col.names=col.names)

  list(votes=votes,
       lawmaker.ips=lawmaker.ips,
       doc.stats=doc.stats,
       global.vector=global.vector)
}

read.lawmaker.stats <- function() {
  lawmaker.stats <- read.csv("/n/fs/topics/users/sgerrish/data/legis/data/v11.1/v11.1.legislators_by_session.csv",
                             as.is=TRUE,
                             col.names=c("UserId",
                               "Session",
                               "First", "Last",
                               "_",
                               "Chamber",
                               "Start",
                               "End",
                               "Party",
                               "State",
                               "Url",
                               "Title"))
  uniquify <- function(x) {
    if (111 %in% x$Session) {
      return(x[x$Session == 111,])
    }
    return(x[order(-x$Session)[1],])
  }
  lawmaker.stats <- ddply(lawmaker.stats, "UserId",
                          uniquify)
  lawmaker.stats$Name <- paste(
    lawmaker.stats$First,
    lawmaker.stats$Last,
    sep=" ")
  lawmaker.stats
}
