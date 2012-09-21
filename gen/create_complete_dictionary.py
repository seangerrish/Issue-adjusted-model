#!/usr/bin/python

import nlp.tokenizer as tokenizer

import re

WORD_RE = re.compile("^[a-z_]+$")

LINUX_WORDS_FILE = "/n/fs/topics/users/sgerrish/data/legis/data/v5/words"
EN_WIKTIONARY_FILE = "/n/fs/topics/users/sgerrish/data/legis/data/v5/enwiktionary-20100629-all-titles-in-ns0"
EN_WIKIPEDIA_TITLES = "/n/fs/topics/users/sgerrish/data/legis/data/v5/enwiki-20100622-all-titles-in-ns0"
OUTPUT_FILE = "/n/fs/topics/users/sgerrish/data/legis/data/v5/dictionary.txt"

ignore_chars = ".,:?'`\"$+-/;%\t<>()0123456789=*\\|{}^_~&[]#@!\x98\x99\xb4\x86\x84\xc3\xb8\xa3\x97\xe6\xce\xb2\xb9\x95\xe4\xaf\xd1\xd5\xd6\x85\xcf\xbf\xa9\xa4\x8d\x8b\xab\xe5\x87\xc5\xd0\xbc\xbb\xb1\x8c\xe8"

def ReadWords(words, filename, by_word):
    f = open(filename, "r")
    for i, l in enumerate(f):
        if i and i % 50000 == 0:
            print "Processing %d." % i
        word = l.strip()
        #word = word.translate(tokenizer.translation_table)
        word = word.lower()
        if not WORD_RE.match(word):
            continue

        if by_word:
            word_list = word.split(" ")
        else:
            word_list = [ word ]
        for w in word_list:
            bad = 0
            if not WORD_RE.match(word):
                #for c in ignore_chars:
                #if word.find(c) >= 0:
                #    bad = 1
                bad = 1
                #print "!%s" % word
            if len(word) == 0:
                bad = 1
            if bad:
                continue

            #print word

            #if word not in words:
            # penalize short words.
            #    words[word] = -((4 - min(len(word), 4)) ** 1.5)

            # In general, a word must occur at least three times in a wikipedia title
            # to be counted.  If it's short, it needs five times in a title, or once
            # in a title and one entry in wiktionary.
            if word in words and "a" in words[word] and not by_word:
                continue
            if word not in words:
                words[word] = { "all": 0.0, "a": 0.0 }
            if "a" not in words[word]:
                words[word]["a"] = 0.0
            if by_word:
                #words[word] += 1.0 / ((6 - min(len(word), 5)) ** 1.5)
                if len(word) <= 4:
                    # Don't bother with words fewer than 5 chars.
                    continue
                if len(word_list) > 1:
                    words[word]["a"] += 1.0 / 15.0
                else:
                    words[word]["a"] += 1.0 / 15.0
            else:
                words[word]["a"] += 1

    for w, v in words.items():
        if "a" in v:
            words[w]["all"] += v["a"]
            del (words[w])["a"]
        
    f.close()


def WriteDict(words, out_filename):
    f = open(out_filename, "w")
    for word, vals in words.items():
        if vals["all"] < 2.0:
            continue
        print >>f, word, vals["all"]

    f.close()


if __name__ == '__main__':
    words = {}
    ReadWords(words, LINUX_WORDS_FILE, False)
    ReadWords(words, EN_WIKIPEDIA_TITLES, True)
    ReadWords(words, EN_WIKTIONARY_FILE, False)
    WriteDict(words, OUTPUT_FILE)
