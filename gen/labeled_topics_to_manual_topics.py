#!/usr/bin/python

import csv
import sys

def ReadDocs():
    docs_labels = {}
    f = open("/n/fs/topics/users/sgerrish/data/legis/data/v11.1/v11.1.billtitles_with_categories.csv",
             "r")
    reader = csv.reader(f)
    for row in reader:
        doc_id, session, number, type, title, labels = row
        labels = labels.split(";")
        docs_labels[doc_id] = labels

    f.close()

    labels = []
    labels_f = open("/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-labeled_topics.dat",
                            "r")
    for row in labels_f:
        label = row.split(",")[0]
        labels.append(label)

    labels_f.close()

    doc_ids_file = open("/n/fs/topics/users/sgerrish/data/legis/data/v12.2/v12.2-train-labels.dat_all",
                        "r")
    doc_ids = []
    for doc_id in doc_ids_file:
        doc_id = doc_id.strip()
        doc_ids.append(doc_id)
    doc_ids_file.close()

    return docs_labels, labels, doc_ids

def WriteLabels(docs_labels, labels, doc_ids, sum_to_one):
    filename = "/n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final_docids_manual_labels%s.gamma"
    if sum_to_one:
        filename = filename % ("_sumtoone")
    else:
        filename = filename % ("")

    manual_labels = open(filename, "w")
    missing_docs = []
    for i, doc_id in enumerate(doc_ids):
        if i % 10 == 0:
            print "processing doc %d." % i
            
        if doc_id not in docs_labels:
            print "Warning: DocId not found: %s." % doc_id
        doc_labels = docs_labels.get(doc_id, [])
        weights = []
        for i, label in enumerate(labels):
            weight = 0.0
            if label in doc_labels:
                weight = 1.0
            weights.append(weight)

        weight_sum = sum(weights)
        if sum_to_one and weight_sum >= 1e-4:
            weights = [ x / weight_sum for x in weights ]

        if weight_sum < 1e-4:
            missing_docs.append(doc_id)
            if sum_to_one:
                weights = [ 1. / len(weights) for x in weights ]
            else:
                weights = [ 0.001 for x in weights ]

        weight_strs = [ "%.5f" % weight for weight in weights ]
        row = " ".join(weight_strs)

        print >>manual_labels, row
    manual_labels.close()

    print "Missing %d docs." % len(missing_docs)
    filename = "/n/fs/topics/users/sgerrish/data/legis/experiments/v12.2/v12.2_labeled_topics/v12.2-labeled_topics-train-all/final_docids_manual_labels_missing_docs.csv"
    f = open(filename, "w")
    for missing_doc in missing_docs:
        print >>f, missing_doc
    f.close()


if __name__ == '__main__':
    print "Reading docs."
    docs_labels, labels, doc_ids = ReadDocs()

    print "Writing labels."
    sum_to_one = False
    if len(sys.argv) > 1 and sys.argv[1] == "sum_to_one":
        sum_to_one = True
    WriteLabels(docs_labels, labels, doc_ids, sum_to_one)

