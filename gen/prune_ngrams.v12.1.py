#!/usr/bin/python

import csv
import math
import sys

NGRAMS_IN = "/n/fs/topics/users/sgerrish/data/legis/data/v12.1/vocabulary_v12.1.txt-00000-of-00001"

WORD_COUNT = 43951958 / 5.0

STOPWORDS_FILE = "/n/fs/topics/users/sgerrish/data/legis/data/v11.1/stop-words.txt"

ANCHORTEXT_FILE = "/n/fs/topics/datasets/wikipedia/derived_data/wikipedia_links.txt"

def AugmentStopwords(stopwords):
    extra_stopwords = [
        "sec", "jan", "feb", "extend", "include", "yield",
        "paragraph", "amend", "amends", "amended", "insert", "prohibits", "prohibit",
        "subparagraph", "subparagraphs", "modify", "ment", "subsequently", "secretary",
        "require", "requirement", "revise", "hr", "pcs",
        "strike", "striking", "describe",
        "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov",
        "dec", "po", "such", "thereto", "whereas",
        "thereon", "floor", "rescind", "bill nov", "equally divide and control",
        "express", "pr", "dec", "procedure", "except", "those", "arise", "under", "clause",
        "continued", "cntain", "with", "as subparagraph", "redesignating", "provide",
        "pursuant", "order", "grant under", "under", "purpose", "subsequently", "mean",
        "reside", "joint resolution", "meaning", "extent",
        "makes", "make", "except" ]
    extra_stopwords = []
    for stopword in extra_stopwords:
        stopwords[stopword] = 1

if __name__ == '__main__':
    anchortext = {}
    anchortext_file = open(ANCHORTEXT_FILE, "r")
    for line in anchortext_file:
        line = line.strip()
        parts = line.split(" ")
        count = parts[0]
        word = " ".join(parts[1:])
        count = math.log(int(count) + 1)
        word = word.lower()
        anchortext[word] = count
    anchortext_file.close()

    stopwords = {}
    stopwords_file = open(STOPWORDS_FILE, "r")
    for word in stopwords_file:
        word = word.strip()
        stopwords[word] = 1
    stopwords_file.close()

    ngrams_in = open(NGRAMS_IN, "r")
    reader = csv.reader(ngrams_in)
    unigrams = {}
    unigram_doc_term_counts = {}
    min_count = 1e10
    for ngram, ngram_count, ngram_docs, count_sum_sq, frequency_sum, total_docs, total_terms in reader:
        parts = ngram.split(" ")

        if len(parts) >= 2:
            continue

        unigrams[ngram] = float(ngram_count) / WORD_COUNT

        unigram_doc_term_counts[ngram] = (float(ngram_count) / WORD_COUNT,
                                          float(ngram_docs) / float(total_docs))

        if min_count > int(ngram_count):
            min_count = int(ngram_count)

    # Allow standard stopwords.
    for term in stopwords:
        if term not in unigram_doc_term_counts:
            unigram_doc_term_counts[term] = (0.01, 0.01)

    AugmentStopwords(stopwords)

    ngrams_in.close()

    ngrams_in = open(NGRAMS_IN, "r")
    reader = csv.reader(ngrams_in)
    for ngram, ngram_count, ngram_docs, count_sum_sq, frequency_sum, total_docs, total_terms in reader:
        parts = ngram.split(" ")

        if len(parts) == 1 and parts[0] in stopwords:
            continue

        if parts[-1] in stopwords:
            continue

        # Consider roman numerals stopwords.  Throw out anything with
        # roman numerals at the beginning or at the end.
        roman_numeral = True
        for letter in parts[0]:
            if letter not in "xvi":
                roman_numeral = False
        if roman_numeral:
            continue

        roman_numeral = True
        for letter in parts[-1]:
            if letter not in "xvi":
                roman_numeral = False
        if roman_numeral:
            continue

        if float(ngram_docs) / float(total_docs) < 0.0001:
            continue
        if float(ngram_docs) / float(total_docs) > 0.15:
            continue
        if float(ngram_count) / WORD_COUNT > 0.01:
            continue
        # Note: this throws out words like "britain".
        if float(ngram_count) / WORD_COUNT < 0.000002:
            continue

        """
        if (len(parts) == 1 and float(frequency_sum) / float(ngram_docs) < 0.0002
            or len(parts) == 2 and float(frequency_sum) / float(ngram_docs) < 0.0002
            or len(parts) == 3 and float(frequency_sum) / float(ngram_docs) < 0.0002
            or len(parts) == 4 and float(frequency_sum) / float(ngram_docs) < 0.0002):
            print "omitting doc for low doc frequency: %s" % ngram
            continue
        
        if abs(float(count_sum_sq) / float(ngram_docs) - 0.001) < 0.01:
            pass
        """
        """
        if float(ngram_count) / float(ngram_docs) < 3.0:
            print "skipping word: %s with weight: %.10f" % (
                ngram,
                float(ngram_count) / float(ngram_docs))
            continue
        """
        """
        score = float(ngram_docs) / float(ngram_count)
        if score > 0.5:
            # print "tossing out %s with score %f." % (ngram, score)
            continue
        """
        score = 0.0

        log_anchortext_count = anchortext.get(ngram, 0.0)
        w = (3.0 * log_anchortext_count - 2.0 * math.log(float(ngram_count) + 1.0)
             + 2.0 * math.log(WORD_COUNT + 1)
             - math.log(float(ngram_docs) + 1)
             + math.log(float(total_docs) + 1))
        if len(parts) == 1:
            print >>sys.stdout, ",".join([str(x) for x in (
                ngram, ngram_count, ngram_docs, log_anchortext_count,
                "0.0", "0.0", "1", float(frequency_sum) / float(ngram_docs))])
            continue
        """if len(parts) == 1:
            print ngram, ngram_count, WORD_COUNT
            sys.exit()
        """

        # Only include ngrams if they don't end in an excluded (i.e., rare) term.
        if parts[-1] in stopwords:
            continue

        if (parts[0] in stopwords or parts[-1] in stopwords
            or len(parts[0]) == 1):
            continue

        product_counts = 1.0
        for i, part in enumerate(parts):
            term_frequency, doc_frequency = unigram_doc_term_counts.get(part, (0.0, 0.0))
            if term_frequency > 0.5 or term_frequency < 0.00001:
                continue

            if i == 0 or i == len(parts) - 1:
                if doc_frequency < 0.00125:
                    continue
                if doc_frequency > 0.15:
                    continue
            
            product_counts *= unigrams.get(part, min_count) / WORD_COUNT

        # How many times do we expect to see this ngram?
        expected_count = product_counts * WORD_COUNT
        ngram_count = float(ngram_count)
        if float(ngram_docs) < 4:
            continue
        
        test = ((ngram_count - expected_count)
                / math.sqrt(expected_count))
        
        """        if (parts[0] in stopwords and
            (len(parts) == 5 and test > 2e27
             or len(parts) == 4 and test > 2e20
             or len(parts) == 3 and test > 2e14
             or len(parts) == 2 and test > 2e8)
            or parts[0] not in stopwords and
            """
        doc_frequency = float(ngram_docs) / float(total_docs)
        if doc_frequency > 0.1:
            continue

        print >>sys.stdout, ",".join([str(x) for x in (
            ngram, ngram_count, ngram_docs,
            log_anchortext_count, str(test), score,
            len(parts), float(frequency_sum) / float(ngram_docs))])

    ngrams_in.close()
