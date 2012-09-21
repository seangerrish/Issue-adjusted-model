#!/usr/bin/python
# Copyright 2010 Sean Gerrish.  All Rights Reserved.
#
# Author: Sean Gerrish
#

""" Sample usage:

# Note that these run locally if you keep the last flag.
./select_vocab_v6.py \
  --mapreduce_input_files=/n/fs/topics/datasets/govtrack/senate_files.txt \
  --mapreduce_output_filename=/n/fs/topics/users/sgerrish/data/legis/vocabulary_v6.txt \
  --mapreduce_number_mappers=1 \
  --mapreduce_number_reducers=1 \
  --mapreduce_run_locally

./select_vocab_v6.py \
  --mapreduce_input_files=/n/fs/topics/datasets/govtrack/senate_files.txt \
  --mapreduce_output_filename=/n/fs/topics/users/sgerrish/data/legis/vocabulary_v6.txt \
  --mapreduce_number_mappers=1 \
  --mapreduce_number_reducers=1 \
  --mapreduce_run_locally
"""

import math
import re
import string
import sys

import cluster.mapreduce as mapreduce
import nlp.tokenizer as tokenizer
from optparse import OptionParser, BadOptionError

WORD_RE = re.compile("^[a-z]+$")

parser = OptionParser()

parser.add_option("--bills_list",
                  type="string",
                  dest="bills_list",
                  default=None)
parser.add_option("--dictionary",
                  type="string",
                  dest="dictionary",
                  default=None)

process_long_opt = parser._process_long_opt
def _process_long_opt(rargs, values):
    try:
        process_long_opt(rargs, values)
    except BadOptionError, m:
        # print "Ignoring bad option error: %s" % m
        pass

parser._process_long_opt = _process_long_opt
OPT, args = parser.parse_args()

NGRAM_SIZE = 5

class Mapper(mapreduce.Mapper):
    """Counts the number of words in each line.

    """
    def Start(self):
        self.ignore_chars = ".,:?'`\"$+-/;%\t<>()0123456789=*\\|{}^_~&[]#@!\x98\x99\xb4\x86\x84\xc3"
        self.stemmer = tokenizer.POSStemmer()
        self.bills_list = None
        if OPT.bills_list:
            print "Reading bills."
            self.bills_list = {}
            f = open(OPT.bills_list, "r")
            for b in f:
                parts = b.split(",")
                if len(parts) == 0:
                    continue
                bill_id = parts[0]
                bill_id = bill_id.strip('"')
                self.bills_list[bill_id] = 1
            f.close()
        self.dictionary = None

        if OPT.dictionary:
            print "Reading dictionary."
            self.dictionary = {}
            f = open(OPT.dictionary, "r")
            for w in f:
                parts = w.split(" ")
                if len(parts) == 0:
                    continue
                self.dictionary[parts[0]] = 1
            f.close()
        self.n = 0

    def Map(self, line):
        self.n += 1

        if self.n % 5000 == 0:
            print "Processing %d." % self.n

        line = line.strip()
        if self.bills_list:
            doc_parts = line.split("/")
            if len(doc_parts) < 10:
                print "Could not parse doc %s." % line
                return
            doc_id = "%s_%s" % (doc_parts[7], doc_parts[9])
            doc_id = doc_id.split(".")[0]
            if doc_id not in self.bills_list:
                return

        doc_file = open(line, "r")

        doc_lines = doc_file.readlines()

        doc_text = ""
        total_number_chars = 0
        total_number_nonlower = 0
        for line in doc_lines:
            if not len(line):
                continue
            line = line.strip()
            if not len(line):
                continue
            total_number_chars += len(line)
            number_nonlower = len([ x for x in line
                                    if (x not in string.ascii_lowercase) ])
            total_number_nonlower += number_nonlower

        background_noise = (float(total_number_nonlower) /
                            float(1.0 + total_number_chars))
        for line in doc_lines:
            if not len(line):
                continue
            line = line.strip()
            if not len(line):
                continue
            number_nonlower = len([ x for x in line
                                    if (x not in string.ascii_lowercase) ])

            penalty = (float(number_nonlower) / len(line)) / background_noise - math.log(len(line) + 1) / 10.0
            if abs(penalty - 1.5) < 0.1:
                pass

            if penalty > 1.5:
                #print >>sys.stderr,penalty
                #print >>sys.stderr,"  nkay: " + line
                #print >>sys.stderr, background_noise
                continue

            line = line.lower()
            if "strike" in line:
                penalty += 0.1
            if "subparagraph" in line:
                penalty += 0.1
            if "section" in line:
                penalty += 0.1
            if "amend" in line:
                penalty += 0.1
            if penalty > 1.4:
                #print penalty
                #print >>sys.stderr,"skipping line:" + line
                continue
            
            doc_text += " " + line

        word_list = {}

        ngram_lists = {}

        doc_number_words = 0
        #            l.encode('ascii', 'replace')
        # l = l.translate(tokenizer.translation_table)
        l = self.stemmer.StemWords(doc_text)

        words = []
        word_counts = {}
        for word in l:
            words.append(word)
            if word not in word_counts:
                word_counts[word] = 0
            word_counts[word] += 1

        for word in words:
            if word_counts[word] < 2:
                continue
            word = word.translate(tokenizer.translation_table)
            word = word.strip()
            word = word.lower()
            bad = 0
            if not WORD_RE.match(word):
                bad = 1
            if self.dictionary and word not in self.dictionary:
                bad = 1
            if bad:
                continue

            if len(word) == 0:
                continue

            for n in range(1, NGRAM_SIZE + 1):
                if n not in ngram_lists:
                    ngram_lists[n] = []
                l = ngram_lists[n]
                l.append(word)
                if len(l) > n:
                    del l[0]

                ngram_string = " ".join(l)

                if len(ngram_string) <= 2:
                    continue

                """
                if not doc_text and len(word):
                doc_text = word
                elif doc_text and len(word):
                doc_text += " " + word
                """
                if ngram_string not in word_list:
                    word_list[ngram_string] = 0
                word_list[ngram_string] += 1
                doc_number_words += 1

        # Output word- and doc- counts for each word.
        doc_length = 0.0
        for word, count in word_list.items():
            doc_length += count

        for word, count in word_list.items():
            self.Output(word, (count, 1, doc_length))

        # Output aggregate counts for the doc.
        self.OutputPreReduce((doc_number_words, 1))
        doc_file.close()


class Reducer(mapreduce.Reducer):
    def PreReduce(self, counts):
        """Count up the total of all docs and all words."""
        stats = self.PreReduceData()
        words, docs = counts
        if "words" not in stats:
            stats["words"] = 0
        stats["words"] += words
        if "docs" not in stats:
            stats["docs"] = 0
        stats["docs"] += docs

        self.n = 0

    def Reduce(self, word, counts):
        """Print aggregate stats for each word."""
        self.n += 1

        #if self.n % 100 == 0:
        #    print "Processing %d." % self.n

        stats = self.PreReduceData()
        word_count = 0.0
        doc_count = 0.0
        count_sum_sq = 0.0
        frequency_sum = 0.0
        for w, d, doc_length in counts:
            count_sum_sq += w * w
            word_count += w
            doc_count += d
            frequency_sum += float(w) / doc_length
        total_words = stats["words"]
        total_docs = stats["docs"]

        # If this term tends to appear only a few times per doc each
        # time it appears, toss it out.
        

        # Get rid of the vast majority of rarities.
        if doc_count <= 3:
            return

        #elif word_count / total_words > 0.0004:
        #    return

        self.Output("%s,%d,%d,%f,%f,%d,%d"
                    % (word,
                       word_count,
                       doc_count,
                       count_sum_sq,
                       frequency_sum,
                       total_docs,
                       total_words))


if __name__ == '__main__':

    # Should always be the first thing called once flags are initialized.
    mapreduce.REGISTER(Mapper(), Reducer())
    
    spec = mapreduce.MapReduceSpecification("count_words")
    controller = mapreduce.MapReduceController(Mapper,
                                               Reducer,
                                               spec)
    controller.Run()

