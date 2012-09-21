vocabulary <- read.csv("/n/fs/topics/users/sgerrish/data/legis/data/v12.2/ngrams_v12.2.csv", as.is=TRUE, header=FALSE)
names(vocabulary)[1] = "Word"

labeled.topics <- read.csv("/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-labeled_topics.dat",
                           as.is=TRUE,
                           header=FALSE)
?write.table
write.table(labeled.topics[, 3:ncol(labeled.topics)],
            sep=" ",
            file="/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-labeled_topics.beta",
            row.names=FALSE,
            col.names=FALSE)

nrow(labeled.topics)

labeled.topic.words <- NULL
for (i in 1:nrow(labeled.topics)) {
  topic.label = labeled.topics[i, 1]
  print(topic.label)
  words.o <- order(-unlist(labeled.topics[i, 3:ncol(labeled.topics)]))
  print(length(words.o))
  print(words.o[1:10])

  print(min(unlist(labeled.topics[i, 3:5002])))
  print(max(unlist(labeled.topics[i, 3:5002])))
  
  top.words <- vocabulary$Word[words.o][1:10]
  row <- data.frame(Category=topic.label,
                    Top10Words=paste(top.words, collapse=","))
  if (is.null(labeled.topic.words)) {
    labeled.topic.words <- row
  } else {
    labeled.topic.words <- rbind(labeled.topic.words,
                                 row)
  }
  labeled.topic.words$Category <- as.character(labeled.topic.words$Category)
  labeled.topic.words$Top10Words <- as.character(labeled.topic.words$Top10Words)
  
}

labeled.topic.words

write.csv(labeled.topic.words,
          file="/n/fs/topics/users/sgerrish/data/legis/data/v12.2/labeled_topic_words.csv")

