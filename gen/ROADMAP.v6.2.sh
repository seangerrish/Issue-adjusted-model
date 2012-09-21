#!/usr/bin/bash
# First, get a list of all bill text.
#
# V6.2: Only take the final vote on a bill in a chamber.
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
cd /n/fs/topics/datasets/govtrack
pushd /
find /n/fs/topics/datasets/govtrack/ \
  | egrep '.*/.../.+/.+txt' \
  > /n/fs/topics/datasets/govtrack/senate_files.txt &

# Next, create the vocabulary file.
# Create vocabulary_v2.
# Format:
# ngram, ngram count, count for docs with ngram, total number of docs, sum of all ngrams

# Select house/senate votes.  6741 votes!

CREATE TABLE scratch.votes4 AS
  SELECT MAX(date) AS date,
    id AS id,
    billtype AS bt,
    billnumber AS bn,
    billsession AS bs
  FROM votes
  WHERE (id LIKE 's%'
      OR id LIKE 'h%')
  AND LOWER(votes.description) NOT LIKE '%table%'
  AND LOWER(votes.description) NOT LIKE '%waive cba%'
  AND LOWER(votes.description) NOT LIKE '%is germane%'
  AND (LOWER(votes.description) LIKE 'on the %resolution%'
       OR LOWER(votes.description) LIKE 'on %passage%'
       OR LOWER(votes.description) LIKE '%motion%ove%ide%veto%'
       OR LOWER(votes.description) LIKE 'on%conference report%'
       OR LOWER(votes.description) LIKE '%motion%cloture%')
  AND NOT ISNULL(billnumber)
#  GROUP BY bt,bn,bs;
  GROUP BY bt,bn,bs,id;

SELECT *
  INTO OUTFILE '/tmp/votes_by_date.csv'
  FIELDS TERMINATED BY ','
  LINES TERMINATED BY '\n'
  FROM scratch.votes4;

# From clearcow.
./latest_votes_by_date.py
./earliest_votes_by_date.py

CREATE TABLE scratch.latest_votes4
  (date DATE,
   id varchar(10) NOT NULL PRIMARY KEY,
   bt varchar(2),
   bn int(11),
   bs int(11));
LOAD DATA INFILE '/tmp/latest_votes_by_date.csv' INTO TABLE scratch.latest_votes4
  FIELDS TERMINATED BY ','
  LINES TERMINATED BY '\r\n';

CREATE TABLE scratch.earliest_votes4
  (date DATE,
   id varchar(10) NOT NULL PRIMARY KEY,
   bt varchar(2),
   bn int(11),
   bs int(11));
LOAD DATA INFILE '/tmp/earliest_votes_by_date.csv' INTO TABLE scratch.earliest_votes4
  FIELDS TERMINATED BY ','
  LINES TERMINATED BY '\r\n';

# 2199548 rows:
SELECT people_votes.personid AS person,
       scratch.latest_votes4.id AS vid,
       scratch.latest_votes4.date AS date,
       people_votes.vote AS vote,
        concat(concat(bs, "_"), concat(bt, bn)) AS bill
  INTO OUTFILE '/tmp/legislator_item_votes_by_date.csv'
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
  FROM scratch.latest_votes4
    INNER JOIN people_votes ON (scratch.latest_votes4.id=people_votes.voteid)
  WHERE NOT ISNULL(people_votes.personid)
  GROUP BY person, vid, date, bill;

# 2199529 rows:
SELECT people_votes.personid AS person,
       scratch.latest_votes4.id AS vid,
       scratch.latest_votes4.date AS date,
       people_votes.vote AS vote,
        concat(concat(bs, "_"), concat(bt, bn)) AS bill
  INTO OUTFILE '/tmp/legislator_votes.csv'
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
  FROM scratch.latest_votes4
    INNER JOIN people_votes ON (scratch.latest_votes4.id=people_votes.voteid)
  WHERE NOT ISNULL(people_votes.personid)
  GROUP BY person, bill;

# Early votes:
# 2199548 rows:
SELECT people_votes.personid AS person,
       scratch.earliest_votes4.id AS vid,
       scratch.earliest_votes4.date AS date,
       people_votes.vote AS vote,
        concat(concat(bs, "_"), concat(bt, bn)) AS bill
  INTO OUTFILE '/tmp/legislator_item_votes_by_date.csv'
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
  FROM scratch.earliest_votes4
    INNER JOIN people_votes ON (scratch.earliest_votes4.id=people_votes.voteid)
  WHERE NOT ISNULL(people_votes.personid)
  GROUP BY person, vid, date, bill;

# 2199529 rows:
SELECT people_votes.personid AS person,
       scratch.earliest_votes4.id AS vid,
       scratch.earliest_votes4.date AS date,
       people_votes.vote AS vote,
        concat(concat(bs, "_"), concat(bt, bn)) AS bill
  INTO OUTFILE '/tmp/legislator_votes.csv'
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
  FROM scratch.earliest_votes4
    INNER JOIN people_votes ON (scratch.earliest_votes4.id=people_votes.voteid)
  WHERE NOT ISNULL(people_votes.personid)
  GROUP BY person, bill;


# 5332 rows.
SELECT concat(concat(bs, "_"), concat(bt, bn)),
      bs, bn, bt, IF(ISNULL(title), "", title)
  INTO OUTFILE '/tmp/billtitles.csv'
    FIELDS TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '\"'
    LINES TERMINATED BY '\n'
  FROM scratch.latest_votes4
  LEFT JOIN billtitles
    ON (billtitles.session = scratch.latest_votes4.bs
        AND number = scratch.latest_votes4.bn
        AND type = scratch.latest_votes4.bt)
  GROUP BY bs,bn,bt;
SELECT concat(concat(bs, "_"), concat(bt, bn)),
      bs, bn, bt, IF(ISNULL(title), "", title)
  INTO OUTFILE '/tmp/billtitles.csv'
    FIELDS TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '\"'
    LINES TERMINATED BY '\n'
  FROM scratch.earliest_votes4
  LEFT JOIN billtitles
    ON (billtitles.session = scratch.earliest_votes4.bs
        AND number = scratch.earliest_votes4.bn
        AND type = scratch.earliest_votes4.bt)
  GROUP BY bs,bn,bt;

# Note: we can use v3 for now, since it depends only on /tmp/billtitles.csv.
./download_bills_v4.py

# 1257 rows.
SELECT people.id, firstname, lastname, MIN(startdate), MAX(enddate), GROUP_CONCAT(DISTINCT(party)), GROUP_CONCAT(DISTINCT(type)), GROUP_CONCAT(DISTINCT(state))
  INTO OUTFILE '/tmp/legislators.csv'
  FIELDS TERMINATED BY ','
  OPTIONALLY ENCLOSED BY '\"'
  LINES TERMINATED BY '\n'
  FROM scratch.latest_votes4
  INNER JOIN people_votes ON (scratch.latest_votes4.id = govtrack.people_votes.voteid)
  LEFT JOIN people ON (people.id=people_votes.personid)
  LEFT JOIN people_roles ON (people.id=people_roles.personid)
  WHERE NOT ISNULL(people.id)
  GROUP BY people.id;
# 1257 rows.
SELECT people.id, firstname, lastname, MIN(startdate), MAX(enddate), GROUP_CONCAT(DISTINCT(party)), GROUP_CONCAT(DISTINCT(type)), GROUP_CONCAT(DISTINCT(state))
  INTO OUTFILE '/tmp/legislators.csv'
  FIELDS TERMINATED BY ','
  OPTIONALLY ENCLOSED BY '\"'
  LINES TERMINATED BY '\n'
  FROM scratch.earliest_votes4
  INNER JOIN people_votes ON (scratch.earliest_votes4.id = govtrack.people_votes.voteid)
  LEFT JOIN people ON (people.id=people_votes.personid)
  LEFT JOIN people_roles ON (people.id=people_roles.personid)
  WHERE NOT ISNULL(people.id)
  GROUP BY people.id;


# TODO.
mkdir /home/sgerrish/n_fs_topics/users/sgerrish/data/legis/data/v6
cp /tmp/legislator_votes.csv /home/sgerrish/n_fs_topics/users/sgerrish/data/legis/data/v6.2/v6.2.legislator_votes.csv
cp /tmp/legislators.csv /home/sgerrish/n_fs_topics/users/sgerrish/data/legis/data/v6.2/v6.2.legislators.csv
cp /tmp/billtitles.csv /home/sgerrish/n_fs_topics/users/sgerrish/data/legis/data/v6.2/v6.2billtitles.csv

pushd /n
find /n/fs/topics/datasets/govtrack/ | grep .txt \
  > /n/fs/topics/datasets/govtrack/senate_bills_amendments.txt
popd

# Create the vocabulary.
# From v5:
# ./create_complete_dictionary.py
cp /n/fs/topics/users/sgerrish/data/legis/data/v5/dictionary.txt /n/fs/topics/users/sgerrish/data/legis/data/v6/dictionary.txt
./select_vocab_v6.py \
  --dictionary=/n/fs/topics/users/sgerrish/data/legis/data/v6/dictionary.txt \
  --mapreduce_input_files=/n/fs/topics/datasets/govtrack/senate_bills_amendments.txt \
  --mapreduce_output_filename=/n/fs/topics/users/sgerrish/data/legis/data/v6/vocabulary_v6.txt \
  --mapreduce_number_mappers=50 \
  --bills_list=/n/fs/topics/users/sgerrish/data/legis/data/v6/v6.billtitles.csv \
  --mapreduce_number_reducers=10
cat /n/fs/topics/users/sgerrish/data/legis/data/v6/vocabulary_v6.txt-000??-of-00010 \
  > /n/fs/topics/users/sgerrish/data/legis/data/v6/vocabulary_v6.1.txt-00000-of-00001

# 4143 ngrams.
# Note that we use the same list of ngrams as in the previous run.
./prune_ngrams.v6.1.py \
  > /n/fs/topics/users/sgerrish/data/legis/data/v6/ngrams_v6.1.txt

# 4915 documents.  Yay!
./create_mult_v6.py \
  --dictionary=/n/fs/topics/users/sgerrish/data/legis/data/v6/dictionary.txt \
  --mapreduce_input_files=/n/fs/topics/datasets/govtrack/senate_bills_amendments.txt \
  --vocabulary_filename=/n/fs/topics/users/sgerrish/data/legis/data/v6/ngrams_v6.1.txt \
  --bills_list=/n/fs/topics/users/sgerrish/data/legis/data/v6/v6.billtitles.csv \
  --mapreduce_output_filename=/n/fs/topics/users/sgerrish/data/legis/data/v6/v6.1-billtext.docline \
  --mult_filename=/n/fs/topics/users/sgerrish/data/legis/data/v6/v6.1-billtext-mult.dat \
  --mapreduce_number_mappers=40 \
  --mapreduce_number_reducers=20

cat /n/fs/topics/users/sgerrish/data/legis/data/v6/v6.1-billtext.docline-000??-of-00020 \
  > /n/fs/topics/users/sgerrish/data/legis/data/v6/v6.1-billtext.docline
cat /n/fs/topics/users/sgerrish/data/legis/data/v6/v6.1-billtext-mult.dat-000??-of-00020 \
  > /n/fs/topics/users/sgerrish/data/legis/data/v6/v6.1-billtext-mult.dat
cat /n/fs/topics/users/sgerrish/data/legis/data/v6/v6.1-billtext-mult.dat-vector-000??-of-00020 \
  > /n/fs/topics/users/sgerrish/data/legis/data/v6/v6.1-billtext-mult.dat-vector

# Next, inspect the vocabulary.
# We have xx total wordsb
# xx total docs

# We can still use v4.2, because it's by 6 folds.
# Not dropped: 4141.
./trim_senators_bills_v4.2.py \
  --bills_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v6/v6.1-billtext-mult.dat \
  --bills_train_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-train-mult.dat \
  --bills_test_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-test-mult.dat \
  --bills_validate_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-validate-mult.dat \
  --votes_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2.legislator_votes.csv \
  --votes_text_train_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-text-train-votes.dat \
  --votes_text_validate_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-text-validate-votes.dat \
  --votes_text_test_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-text-test-votes.dat \
  --votes_test_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-test-votes.dat \
  --votes_train_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-train-votes.dat \
  --votes_validate_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-validate-votes.dat \
  --senators_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2.legislators.csv \
  --senators_filename_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-users.dat

# Create a time-series dataset
# (interrupted)
./trim_senators_bills_v5.py \
  --bills_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v6/v6.1-billtext-mult.dat \
  --bills_train_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-train-time-series-mult.dat \
  --bills_validate_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-validate-time-series-mult.dat \
  --votes_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2.legislator_votes.csv \
  --votes_test_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-test-votes.dat \
  --votes_train_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-train-votes.dat \
  --votes_train_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-train-time-series-votes.dat \
  --votes_validate_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-validate-votes.dat \
  --votes_validate_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-validate-time-series-votes.dat \
  --senators_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2.legislators.csv \
  --senators_filename_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-users.dat

# Create a time-series dataset.
./trim_senators_bills_v5.2.py \
  --bills_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v6/v6.1-billtext-mult.dat \
  --bills_train_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-train-time-series-session-mult.dat \
  --bills_validate_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-validate-time-series-session-mult.dat \
  --votes_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2.legislator_votes.csv \
  --votes_train_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-train-time-series-session-votes.dat \
  --votes_validate_time_series_out=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2-validate-time-series-session-votes.dat \
  --senators_filename_in=/n/fs/topics/users/sgerrish/data/legis/data/v6.2/v6.2.legislators.csv

# For run with users -- l2-regularized (note that this won't work,
# since we now have more files in this directory).
mkdir ~/src100/legis/runs/026
cat user_doc_predictions_*_*0.dat | grep ",${session}_" \
    | grep -v UserId \
    > ~/src100/legis/runs/026/user_doc_predictions_session.csv;

for session in `seq 103 111`; do
  echo ${session}
  cat user_doc_predictions_*_*0.dat | grep ",${session}_" \
    > ~/src100/legis/runs/026/user_doc_predictions_session_${session}.csv;
done


cat user_doc_predictions_*_*_l1.dat | grep ",${session}_" \
    | grep -v UserId \
    > ~/src100/legis/runs/026/user_doc_predictions_session_l1.csv;

for session in `seq 103 111`; do
  echo ${session}
  cat user_doc_predictions_*_*_l1.dat | grep ",${session}_" \
    > ~/src100/legis/runs/026/user_doc_predictions_session_l1_${session}.csv;
done

# For topic experiments:
mkdir ~/src100/legis/runs/027

# For collated experiments:
mkdir ~/src100/legis/runs/028
