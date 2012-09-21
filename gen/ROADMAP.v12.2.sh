#!/usr/bin/bash
# This is a branch off of v6.2.
#
# v12.1: house and senate votes.  Further-trimmed vocabulary from v11.1.
#
# v11.3: Same as v11.2, but with a vocabulary selected to be better on
#  subset 0, session 11.
# v11.2: Adding "on motion to concur in" as an
#  allowable "on passage" vote description.
#
# v11.1: house and senate votes.  Based on first-vote.
#
# v10.2: house-only votes.  based on first-vote.  Uses a
#  vocabulary much more similar to old vocabulary.
#
# v8.1: senate-only votes. based on first- vote.
# v8.2: house-only votes. based on first- vote.
# v7.1: senate-only votes. Otherwise based on v6.2.
#
# v7.2: house-only votes.  Otherwise based on v6.2.
#
# v6.1: generated with improved vocabulary (fewer stopwords, most
# boilerplate/procedural text removed).
#
# v5.2: generated with improved vocabulary (fewer stopwords)
# Differs from v5 in that we consider about 2-3k more documents, most
# of which are longer (probably more amendments).
# Differs from v4.3 in that we more aggressively remove nonsense words.
#
# v2.1: with ngrams
# v2.2: without ngrams
# (In both cases, we aimed for similar numbers of words)
#
# Note that the bills for v6.2 are exactly the same as those for v6.1,
# and that votes are the only difference.


# TODO.
mkdir /home/sgerrish/n_fs_topics/users/sgerrish/data/legis/data/v12.1
cp /tmp/legislator_votes.csv /home/sgerrish/n_fs_topics/users/sgerrish/data/legis/data/v12.1/v12.1.legislator_votes.csv
cp /tmp/legislators.csv /home/sgerrish/n_fs_topics/users/sgerrish/data/legis/data/v12.1/v12.1.legislators.csv
cp /tmp/billtitles.csv /home/sgerrish/n_fs_topics/users/sgerrish/data/legis/data/v12.1/v12.1.billtitles.csv

# Create the vocabulary.
# From v5:
# ./create_complete_dictionary.py
cp /n/fs/topics/users/sgerrish/data/legis/data/v5/dictionary.txt /n/fs/topics/users/sgerrish/data/legis/data/v12.1/dictionary.txt

./select_vocab_v12.py \
  --dictionary=/n/fs/topics/users/sgerrish/data/legis/data/v6/dictionary.txt \
  --mapreduce_input_files=/n/fs/topics/datasets/govtrack/senate_bills_amendments.txt \
  --mapreduce_output_filename=/n/fs/topics/users/sgerrish/data/legis/data/v12.1/vocabulary_v12.txt \
  --mapreduce_number_mappers=50 \
  --bills_list=/n/fs/topics/users/sgerrish/data/legis/data/v12.1/v12.1.billtitles.csv \
  --mapreduce_number_reducers=10

cat /n/fs/topics/users/sgerrish/data/legis/data/v12.1/vocabulary_v12.txt-000??-of-00010 \
  > /n/fs/topics/users/sgerrish/data/legis/data/v12.1/vocabulary_v12.1.txt-00000-of-00001

# 4743 ngrams.
# Note that we use the same list of ngrams as in the previous run.
./prune_ngrams.v12.1.py \
  > /n/fs/topics/users/sgerrish/data/legis/data/v12.1/ngrams_v12.2.txt
# Run analyze_vocab.v12.1.r and copy the resulting file to the data directory.
cp ngrams.v12.2.csv /n/fs/topics/users/sgerrish/data/legis/data/v12.2/ngrams_v12.2.csv
rm /n/fs/topics/users/sgerrish/data/legis/data/v12.2/ngrams_v12.2.txt

# 4915 documents.  Yay!
./create_mult_v6.py \
  --dictionary=/n/fs/topics/users/sgerrish/data/legis/data/v6/dictionary.txt \
  --mapreduce_input_files=/n/fs/topics/datasets/govtrack/senate_bills_amendments.txt \
  --vocabulary_filename=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/ngrams_v12.2.csv \
  --bills_list=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2.billtitles.csv \
  --mapreduce_output_filename=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-billtext.docline \
  --mult_filename=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-billtext-mult.dat \
  --mapreduce_number_mappers=100 \
  --mapreduce_number_reducers=20

cat /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-billtext.docline-000??-of-00020 \
  > /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-billtext.docline
cat /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-billtext-mult.dat-000??-of-00020 \
  > /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-billtext-mult.dat
cat /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-billtext-mult.dat-vector-000??-of-00020 \
  > /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-billtext-mult.dat-vector

./fetch_subject_terms.py \
  /n/fs/topics/users/sgerrish/data/legis/data/v11.1/v11.1.billtitles.csv \
  /n/fs/topics/users/sgerrish/data/legis/data/v11.1/v11.1.billtitles_with_categories.csv \
  /n/fs/topics/users/sgerrish/data/legis/data/v11.1/v11.1.billcategories.txt

./create_labeled_topics_v12.py \
  --dictionary=/n/fs/topics/users/sgerrish/data/legis/data/v6/dictionary.txt \
  --mapreduce_input_files=/n/fs/topics/datasets/govtrack/senate_bills_amendments.txt \
  --vocabulary_filename=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/ngrams_v12.2.csv \
  --bills_list=/n/fs/topics/users/sgerrish/data/legis/data/v11.1/v11.1.billtitles_with_categories.csv \
  --mapreduce_output_filename=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-labeled_topics \
  --mapreduce_number_mappers=40 \
  --mapreduce_number_reducers=20

cat /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-labeled_topics-000??-of-00020 \
  > /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-labeled_topics.dat

# Convert the set of docs with labels to
# topics.
./labeled_topics_to_manual_topics.py

# Next, inspect the vocabulary.
# We have xx total words
# we have 5000 total words.
# We have xx total docs.
# How many topics?
# Combine the topics and analyze them.

# cat /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-labeled_topics* | wc -l
# There are 74 distinct topics.

#cat /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-labeled_topics* > /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-labeled_topics.dat

# Create topic descriptions and then output topics.
# analyze_labeled_topics.r

# Use standard lda-c (written by David Blei and provided on his website).
mkdir /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics
cp /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-labeled_topics.beta \
    /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics
for subset in all 0 1 2 3 4 5; do
    rm -rf /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics.other
    echo "num_topics 74" > /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics.other
    echo "num_terms 5000" >> /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics.other
    echo "alpha 0.01" >> /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics.other

    cat /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-train-mult.dat_${subset} \
	| ./convert_mult_to_lda.py \
	> /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-train-mult.dat_${subset}

    ../src/lda-c-dist/lda \
	est \
	0.0135 \
	74 \
	/n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/settings.txt \
	/n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-train-mult.dat_${subset} \
	/n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics \
	/n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-${subset}
done

mkdir /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_vanilla_lda_alpha_1byk
rm -rf /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-vanilla_lda_alpha_1byk.other
echo "num_topics 74" > /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-vanilla_lda_alpha_1byk.other
echo "num_terms 5000" >> /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-vanilla_lda_alpha_1byk.other
echo "alpha 0.0135" >> /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-vanilla_lda_alpha_1byk.other
for subset in all 0 1 2 3 4 5; do
#    ../src/lda-c-dist/lda \
    CMD="../src/lda-c-dist/lda \
	est \
	0.0135 \
	74 \
	/n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_vanilla_lda_alpha_1byk/settings.txt \
	/n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-train-mult.dat_${subset} \
	seeded \
	/n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_vanilla_lda_alpha_1byk/v12.2-vanilla_lda_alpha_1byk-train-${subset}"
    echo ${CMD}
    echo "cd `pwd`; ${CMD};" | qsub.py
done

# It was unnecessary to do this for subsets 0, ..., 5.  However, we do want the "all" subset.
# Let's inspect the topics.
analyze_labeled_topics_two_iterations.r

# Looking good!  Next, create a gammas file out of the doc ids and the gammas output file.
cut -f1 -d' ' /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-train-mult.dat_all \
  > /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-train-labels.dat_all
rm -rf /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final_docids.gamma
paste --delimiters=" " \
  /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-train-labels.dat_all
  /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma \
  > /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final_docids.gamma


# Next, create the gammas file for the standard LDA topics.
rm -rf /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_vanilla_lda_alpha_1byk/v12.2-vanilla_lda_alpha_1byk-train-all/final_docids.gamma
paste --delimiters=" " \
   /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-train-labels.dat_all
   /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_vanilla_lda_alpha_1byk/v12.2-vanilla_lda_alpha_1byk-train-all/final.gamma \
  > /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_vanilla_lda_alpha_1byk/v12.2-vanilla_lda_alpha_1byk-train-all/final_docids.gamma

# Create a gammas file with 1 when the topic is present and 0 when it is not.

# /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma

# We can still use v4.2, because it's by 6 folds.
# Not dropped: 4449.
./trim_senators_bills_v4.2.py \
  --bills_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-billtext-mult.dat \
  --bills_train_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-train-mult.dat \
  --bills_test_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-test-mult.dat \
  --bills_validate_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-validate-mult.dat \
  --votes_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2.legislator_votes.csv \
  --votes_text_train_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-text-train-votes.dat \
  --votes_text_validate_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-text-validate-votes.dat \
  --votes_text_test_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-text-test-votes.dat \
  --votes_test_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-test-votes.dat \
  --votes_train_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-train-votes.dat \
  --votes_validate_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-validate-votes.dat \
  --senators_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2.legislators.csv \
  --senators_filename_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-users.dat

# Create a time-series dataset
# (interrupted)
./trim_senators_bills_v5.py \
  --bills_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-billtext-mult.dat \
  --bills_train_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-train-time-series-mult.dat \
  --bills_validate_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-validate-time-series-mult.dat \
  --votes_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2.legislator_votes.csv \
  --votes_test_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-test-votes.dat \
  --votes_train_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-train-votes.dat \
  --votes_train_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-train-time-series-votes.dat \
  --votes_validate_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-validate-votes.dat \
  --votes_validate_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-validate-time-series-votes.dat \
  --senators_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2.legislators.csv \
  --senators_filename_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-users.dat

# Create a time-series dataset.
./trim_senators_bills_v7_time.py \
  --bills_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-billtext-mult.dat \
  --bills_train_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-train-time-series-session-mult.dat \
  --bills_validate_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-validate-time-series-session-mult.dat \
  --votes_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2.legislator_votes.csv \
  --votes_train_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-train-time-series-session-votes.dat \
  --votes_validate_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-validate-time-series-session-votes.dat \
  --senators_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2.legislators.csv

## Copy relevant files to local directory.


# Create the shuffled datasets.
cat /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-billtext-mult.dat | cut -f1 -d' ' > /n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-billtext-ids.dat

./shuffle_topics.py /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma.shuffled.1 1

./shuffle_topics.py /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma.shuffled.2 2

./shuffle_topics.py /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma.shuffled.3 3

./shuffle_topics.py /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma.shuffled.4 4

./shuffle_topics.py /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma.shuffled.5 5


./shuffle_topics_by_row.py /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma.shuffledbyrow.1 1

./shuffle_topics_by_row.py /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma.shuffledbyrow.2 2

./shuffle_topics_by_row.py /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma.shuffledbyrow.3 3

./shuffle_topics_by_row.py /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma.shuffledbyrow.4 4

./shuffle_topics_by_row.py /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma.shuffledbyrow.5 5

for i in `seq 1 100`; do
    ./shuffle_topics_by_row.py /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma /n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final.gamma.shuffledbyrow.${i} ${i}
done


# Unfortunately, some votes are in the House or Senate and we're not separating them correctly.  Here's how we'll do it:
# 1. Create a scratch table with votes from sessions 106-111.
# 2. Join this with peoplevotes
# 3. Read in this list of peoples and chambers when we perform inference.
#    to perform inference.

mysql govtrack -uroot

# Create a temporary table with all of our votes (including
# information on chamber), then copy them to the correct directory.

CREATE TABLE scratch.votes_with_people_and_docs
  SELECT personid, voteid, billsession, billtype, billnumber,
  CONCAT(billsession, "_", billtype, billnumber)
  FROM votes
  INNER JOIN people_votes
    ON (people_votes.voteid = votes.id)
  WHERE votes.billsession >= 106;

SELECT * FROM scratch.votes_with_people_and_docs
  INTO OUTFILE "/tmp/votes_with_chamber.csv"
  FIELDS TERMINATED BY ",";

cp /tmp/votes_with_chamber.csv ~/n_fs_topics/users/sgerrish/data/legis/data/v12.2/v12.2


