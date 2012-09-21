#!/usr/bin/python
# Copyright 2010 Sean Gerrish.  All Rights Reserved.
#
# Author: Sean Gerrish
#

""" Sample usage:

# Note that these run locally if you keep the last flag.
./create_mult_v1.py \
  --mapreduce_input_files=/n/fs/topics/datasets/govtrack/senate_files.txt \
  --vocabulary_filename=/n/fs/topics/users/sgerrish/data/legis/vocabulary_v1.txt-00000-of-00001 \
  --mapreduce_output_filename=/n/fs/topics/users/sgerrish/data/legis/billtext.docline \
  --mult_filename=/n/fs/topics/users/sgerrish/data/legis/billtext-mult.dat \
  --mapreduce_number_mappers=1 \
  --mapreduce_number_reducers=1 \
  --mapreduce_run_locally
"""

import os
import re
import socket
import sys

from optparse import OptionParser, BadOptionError

import cluster.mapreduce as mapreduce
import nlp.tokenizer as tokenizer

WORD_RE = re.compile("^[a-z]+$")

parser = OptionParser()
parser.add_option("--vocabulary_filename",
                  default="",
                  type="string",
                  dest="vocabulary_filename")
parser.add_option("--mult_filename",
                  default="",
                  type="string",
                  dest="mult_filename")
parser.add_option("--bills_list",
                  type="string",
                  dest="bills_list",
                  default=None)
parser.add_option("--dictionary",
                  type="string",
                  dest="dictionary",
                  default=None)

# Allow nonexistent args to be skipped.
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
        self.short_docs = 0

        f = open("/proc/cpuinfo", "r")
        for l in f:
           #print >>sys.stderr, l,
           pass
        f.close()
        self.f = open("/u/sgerrish/tmp/%d.%s" % (self._mapper_number, socket.gethostname()), "w")
        self.f.close()
        
        self.ignore_chars = ".,:?'`\"$+-/;%\t<>()0123456789=*\\|{}^_~&[]#@!\x98\x99\xb4\x86\x84\xc3"
        self.stemmer = tokenizer.POSStemmer()
        self.vocabulary = {}
        self.ngrams = {}
        self.max_ngram_count = 0
        vocab_file = open(OPT.vocabulary_filename, "r")        
        for i, line in enumerate(vocab_file):
            line = line.strip()
            ngram_str = line.split(",")[0]
            ngram = ngram_str.split(" ")
            self.ngrams[tuple(ngram)] = i
            if len(ngram) > self.max_ngram_count:
                self.max_ngram_count = len(ngram)
        vocab_file.close()

        self.bills_list = None
        if OPT.bills_list:
            print "Reading bills."
            f = open(OPT.bills_list)
            self.bills_list = {}
            for b in f:
                parts = b.split(",")
                if len(parts) == 0:
                    print "Illegally formatted bill."
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

        if self.n % 100 == 0:
            print "Processing %d." % self.n
            
        line = line.strip()

        doc_parts = line.split("/")
        if len(doc_parts) < 10:
            print "Illegal document id: %s" % line
            return
        number = doc_parts[9]
        number = number.rstrip(".txt")
        if len(number) == 0:
            print "Illegally formatted bill."
            return
        doc_id = "%s_%s" % (doc_parts[7], number)

        if self.bills_list and doc_id not in self.bills_list:
            print "docid not found."
            return

        doc_file = open(line, "r")

        doc_text = doc_file.read()
        word_list = {}

        ngram_lists = {}

        doc_number_words = 0
        #            l.encode('ascii', 'replace')
        # l = l.translate(tokenizer.translation_table)
        l = self.stemmer.StemWords(doc_text)

        doc_map = {}
        doc_text = ""
        history = []


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

            history.append(word)
        word_count = len(history)

        i = 0
        while i < len(history):
            word_count += 1
            history_length = min(len(history) - i, self.max_ngram_count)
            ngram_length = 1
            ngram = None
            ngram_text = None
            for j in range(history_length, 0, -1):
                ngram_candidate = history[i:i + j]
                ngram = self.ngrams.get(tuple(ngram_candidate), None)
                if ngram is not None:
                    ngram_length = j
                    ngram_text = "_".join(ngram_candidate)
                    # print "found ngram: " + str(ngram)
                    break

            if ngram == None:
                # print "No ngram found: %s" % ngram
                i += 1
                continue

            i += ngram_length

            if ngram not in doc_map:
                doc_map[ngram] = 0

            if len(doc_map):
                doc_text += " "
                # print ngram

            doc_map[ngram] += 1
            doc_text += ngram_text

        # Output word- and doc- counts for each word, but only for
        # those docs with at least 10 unique words.
        if len(doc_map) < 8:
            self.short_docs += 1
            return

        self.Output(doc_id, (doc_text, doc_map))

        if self.short_docs % 20 == 0:
            print "Number of short docs: %d" % self.short_docs


class Reducer(mapreduce.Reducer):
    def Start(self):
        self.ngrams = {}
        vocab_file = open(OPT.vocabulary_filename, "r")        
        for i, line in enumerate(vocab_file):
            line = line.strip()
            ngram_str = line.split(",")[0]
            ngram = ngram_str.split(" ")
            self.ngrams[tuple(ngram)] = i
        vocab_file.close()

        self.mult_file = open("%s-%05d-of-%05d"
                              % (OPT.mult_filename,
                                 self.reducer_number,
                                 self._number_reducers),
                              "w")
        self.vector_file = open("%s-vector-%05d-of-%05d"
                                % (OPT.mult_filename,
                                   self.reducer_number,
                                   self._number_reducers),
                                "w")
        
    def Reduce(self, docid, doctext_docmap):
        """Print aggregate stats for each word."""
        doc_text, doc_map = doctext_docmap[0]

        self.Output("%s %s"
                    % (docid, doc_text))

        term_counts = [ "%d:%d" % (x, y) for (x, y) in doc_map.items() ]
        print >>self.mult_file, "%s %s" % (docid, ' '.join(term_counts))

        term_counts_vector = []
        for i in range(len(self.ngrams)):
            count = doc_map.get(i, 0)
            term_counts_vector.append(count)

        term_counts = [ "%d" % x for x in term_counts_vector ]
        print >>self.vector_file, "%s %s" % (docid, ' '.join(term_counts))

    def Done(self):
        self.mult_file.close()
        self.vector_file.close()

if __name__ == '__main__':

    # Should always be the first thing called once flags are initialized.
    mapreduce.REGISTER(Mapper(), Reducer())
    
    spec = mapreduce.MapReduceSpecification("count_words")
    controller = mapreduce.MapReduceController(Mapper,
                                               Reducer,
                                               spec)
    #controller.resources = 'walltime=0:08:00,mem=9000mb,ncpus=2'
    controller.resources = 'walltime=0:08:00,mem=8000mb'    
    controller.Run()
