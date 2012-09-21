#!/usr/bin/python

# /n/fs/topics/users/sgerrish/data/legis/data/v11.1/v11.1.billtitles.csv

import csv
import re
import sys
import urllib

SUBJECT_TERM_RE = re.compile("<a href=[^>]*subjects.xpd[^>]+>([^<]+)<")

if __name__ == '__main__':
    billtitles_filename = sys.argv[1]
    billtitles_file = open(billtitles_filename, "r")
    reader = csv.reader(billtitles_file)

    out_filename = sys.argv[2]
    billtitles_out_file = open(out_filename, "w")
    writer = csv.writer(billtitles_out_file)

    all_categories = {}
    for i, (doc_id, session, number, type, title) in enumerate(reader):
        if i and i % 200 == 0:
            print "Processing doc %d." % i
        categories = []
        url = "http://www.govtrack.us/congress/bill.xpd?bill=%s%s-%s&tab=related" % (
            type, session, number)
        page_text = urllib.urlopen(url).read()
        m = SUBJECT_TERM_RE.search(page_text)
        while m:
            c = m.groups()[0]
            categories.append(c)
            all_categories[c] = True
            m = SUBJECT_TERM_RE.search(page_text, m.end())
        categories_str = ";".join(categories)
        writer.writerow([doc_id, session, number, type, title, categories_str])

    billtitles_file.close()
    billtitles_out_file.close()

    categories_file = open(sys.argv[3], "w")
    for category in all_categories:
        print >>categories_file, category
    categories_file.close()
