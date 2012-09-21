#!/usr/bin/python

import copy
import csv
import math
import random
import sys
import time

from optparse import OptionParser

parser = OptionParser()

parser.add_option("--bills_filename_in",
                  type="string",
                  dest="bills_filename_in")
parser.add_option("--bills_train_out",
                  type="string",
                  dest="bills_train_out")
parser.add_option("--bills_train_time_series_out",
                  type="string",
                  dest="bills_train_time_series_out")
parser.add_option("--bills_validate_out",
                  type="string",
                  dest="bills_validate_out")
parser.add_option("--bills_validate_time_series_out",
                  type="string",
                  dest="bills_validate_time_series_out")
parser.add_option("--bills_test_out",
                  type="string",
                  dest="bills_test_out")
parser.add_option("--votes_filename_in",
                  type="string",
                  dest="votes_filename_in")
parser.add_option("--votes_text_train_out",
                  type="string",
                  dest="votes_text_train_out")
parser.add_option("--votes_text_validate_out",
                  type="string",
                  dest="votes_text_validate_out")
parser.add_option("--votes_text_test_out",
                  type="string",
                  dest="votes_text_test_out")
parser.add_option("--votes_train_out",
                  type="string",
                  dest="votes_train_out")
parser.add_option("--votes_train_time_series_out",
                  type="string",
                  dest="votes_train_time_series_out")
parser.add_option("--votes_validate_out",
                  type="string",
                  dest="votes_validate_out")
parser.add_option("--votes_validate_time_series_out",
                  type="string",
                  dest="votes_validate_time_series_out")
parser.add_option("--votes_test_out",
                  type="string",
                  dest="votes_test_out")
parser.add_option("--senators_filename_in",
                  type="string",
                  dest="senators_filename_in")
parser.add_option("--senators_filename_out",
                  type="string",
                  dest="senators_filename_out")

# A senator or bill must be on one of these two lists to be included.
#parser.add_option("--senators_list",
#                  type="string",
#                  dest="senators_list")
#parser.add_option("--bills_list",
#                  type="string",
#                  dest="bills_list")

OPT, args = parser.parse_args()
NUMBER_SUBSETS = 6

def ReadVotes(votes, senators, bills):
    f = open(OPT.votes_filename_in, "r")
    reader = csv.reader(f)
    for person_id, vote_id, date, vote, bill_id in reader:
        votes[(person_id, bill_id)] = (vote, date)
        senators[person_id] = 0

        # Increment the number of positive or negative votes on this
        # bill.
        if bill_id not in bills:
            bills[bill_id] = {"+": 0, "-": 0, "voted": (None, None)}
        bills[bill_id][vote] = bills[bill_id].get(vote, 0) + 1
        
    f.close()

def TrimSenators(senators_voted):
    f_in = open(OPT.senators_filename_in, "r")
    f_out = open(OPT.senators_filename_out, "w")
    reader = csv.reader(f_in)
    for row in reader:
        person_id = row[0]
        for i in range(1, len(row)):
            if "|" in row[i]:
                row[i] = row[i].split("|")[1]
            if "," in row[i]:
                row[i] = row[i].replace(",", "_")
                #                print row[i]
        if person_id not in senators_voted:
            continue
        senators_voted[person_id] = 1

        print >>f_out, "%s,%s" % (person_id, "|".join(row[1:]))
    f_in.close()
    f_out.close()

def TrimBills(bills_voted):

    f_in = open(OPT.bills_filename_in, "r")
    f_train_out = {}
    f_validate_out = {}
    f_test_out = open(OPT.bills_test_out, "w")
    for i in range(NUMBER_SUBSETS):
        f_validate_out[i] = open("%s_%d" % (OPT.bills_validate_out, i), "w")
        f_train_out[i] = open("%s_%d" % (OPT.bills_train_out, i), "w")
    f_train_out["all"] = open("%s_%s" % (OPT.bills_train_out, "all"), "w")
    number_bills_dropped = {"no votes": 0,
                            "few votes": 0,
                            "sum votes": 0,
                            "not dropped": 0.0 }
    lines = []
    for line in f_in:
        lines.append(line)
    random.shuffle(lines)

    for subset_index, line in enumerate(lines):
        line = line.strip()
        parts = line.split(" ")
        bill_id = parts[0]
        if bill_id not in bills_voted:
            number_bills_dropped["no votes"] += 1
            if (random.random() < 0.001):
                print bill_id
            continue

        votes = bills_voted.get(bill_id)
        """
        if votes["+"] <= 1 or votes["-"] <= 1:
            number_bills_dropped["few votes"] += 1.0
            number_bills_dropped["sum votes"] += votes["+"] + votes["-"]
            continue
        """

        if votes["+"] + votes["-"] <= 5:
            number_bills_dropped["few votes"] += 1.0
            number_bills_dropped["sum votes"] += votes["+"] + votes["-"]
            continue

        number_bills_dropped["not dropped"] += 1.0

        number_test = 0
        subset = subset_index % (NUMBER_SUBSETS + number_test)
        
        if subset < number_test:
            bills_voted[bill_id]["voted"] = ("test", None)
            print >>f_test_out, line
        else:
            subset = subset - number_test
            bills_voted[bill_id]["voted"] = ("validate", subset)
            print >>f_validate_out[subset], line

            print >>f_train_out["all"], line
            for i in range(NUMBER_SUBSETS):
                if i != subset:
                    print >>f_train_out[i], line

    for reason, count in number_bills_dropped.items():
        print "%s: %d" % (reason, count)
    # print number_bills_dropped["sum votes"] / (number_bills_dropped["few votes"] + number_bills_dropped["

    f_in.close()
    for file in f_validate_out.values():
        file.close()
    for file in f_train_out.values():
        file.close()
    f_test_out.close()


def TrimBillsTimeSeries(votes, bills_voted_time_series):
    # Get a list of bills' vote dates.
    bill_dates = {}
    min_time = 1e10
    max_time = 0
    for (_, bill_id), (_, date) in votes.items():
        if bill_id in bill_dates:
            continue
        try:
            date = time.strptime(date, "%Y-%m-%d %H:%M:%S")
        except:
            date = time.strptime(date, "%Y-%m-%d")

        bill_dates[bill_id] = date
        date_secs = time.mktime(date)
        if min_time > date_secs:
            min_time = date_secs
        if max_time < date_secs:
            max_time = date_secs

    def SubsetFromDate(date, min_time=min_time, max_time=max_time):
        #        print date
        date_secs = time.mktime(date)
        VALIDATION_DAYS = 90
        total_diff = int((max_time - min_time) / (60 * 60 * 24)) / VALIDATION_DAYS

        # Number of 60-day intervals.
        current_month_diff = int((date_secs - min_time) / (60 * 60 * 24)) / VALIDATION_DAYS
        validation_month_time = current_month_diff * VALIDATION_DAYS * (24 * 60 * 60) + min_time
        validation_subset = time.strftime("%Y-%m-%d", time.localtime(validation_month_time))

        train_subsets = []
        for i in range(current_month_diff + 1, total_diff + 1):
            train_month_time = i * VALIDATION_DAYS * (24 * 60 * 60) + min_time
            
            date_string = time.strftime("%Y-%m-%d", time.localtime(train_month_time))
            train_subsets.append(date_string)

        if current_month_diff == 0:
            validation_subset = None
        return (train_subsets, validation_subset)

        
    f_train_time_series_out = {}
    f_validate_time_series_out = {}

    number_bills_dropped = {"no votes": 0,
                            "few votes": 0,
                            "sum votes": 0,
                            "not dropped": 0.0 }

    f_in = open(OPT.bills_filename_in, "r")
    for line in f_in:
        line = line.strip()
        parts = line.split(" ")
        bill_id = parts[0]

        votes_ = bills_voted_time_series.get(bill_id)

        if bill_id not in bills_voted_time_series:
            number_bills_dropped["no votes"] += 1
            continue
        votes = bills_voted.get(bill_id)

        if votes["+"] + votes["-"] <= 5:
            number_bills_dropped["few votes"] += 1.0
            number_bills_dropped["sum votes"] += votes["+"] + votes["-"]
            continue

        date = bill_dates[bill_id]
        train_subsets, validate_subset = SubsetFromDate(date)

        if validate_subset:
            if validate_subset not in f_validate_time_series_out:
                f_validate_time_series_out[validate_subset] = (
                    open("%s_%s" % (OPT.bills_validate_time_series_out, validate_subset), "w"))
            print >> f_validate_time_series_out[validate_subset], line

        for train_subset in train_subsets:
            if train_subset not in f_train_time_series_out:
                f_train_time_series_out[train_subset] = (
                    open("%s_%s" % (OPT.bills_train_time_series_out, train_subset), "w"))

        for train_subset in train_subsets:
            print >> f_train_time_series_out[train_subset], line

        bills_voted_time_series[bill_id]["voted"] = (train_subsets, validate_subset)

    f_in.close()
    for file in f_validate_time_series_out.values():
        file.close()
    for file in f_train_time_series_out.values():
        file.close()

def WriteVotesTrimmed(votes, bills_voted, senators_voted):
    f_bill_test = open(OPT.votes_text_test_out, "w")
    f_vote_test = open(OPT.votes_test_out, "w")
    f_vote_train = {}
    f_bill_validate = {}
    f_bill_train = {}
    f_vote_validate = {}

    for i in range(NUMBER_SUBSETS):
        f_vote_validate[i] = open("%s_%d" % (OPT.votes_validate_out, i), "w")
        f_vote_train[i] = open("%s_%d" % (OPT.votes_train_out, i), "w")
    f_vote_train["all"] = open("%s_%s" % (OPT.votes_train_out, "all"), "w")

    for i in range(NUMBER_SUBSETS):
        f_bill_train[i] = open("%s_%d" % (OPT.votes_text_train_out, i), "w")
        f_bill_validate[i] = open("%s_%d" % (OPT.votes_text_validate_out, i), "w")

    for (person_id, bill_id), (vote, date) in votes.items():
        # If we there are no votes by this senator, continue.
        if senators_voted.get(person_id, 0) == 0:
            continue

        # If there are no votes for this bill, continue.
        use, subset = bills_voted.get(bill_id, {"voted": (None, None)})["voted"]
        if use == None:
            # There was either no vote seen or not enough votes.
            continue

        vote_subset = math.floor(random.random() * NUMBER_SUBSETS)
        if vote_subset == NUMBER_SUBSETS:
            vote_subset = 0

        elif use == "test":
            print >>f_bill_test, "%s,%s,%s" % (vote, bill_id, person_id)
            print >>f_vote_test, "%s,%s,%s" % (vote, bill_id, person_id)
        elif use == "validate":
            print >>f_bill_validate[subset], "%s,%s,%s" % (vote, bill_id, person_id)
            print >>f_vote_validate[vote_subset], "%s,%s,%s" % (vote, bill_id, person_id)
            for i in range(NUMBER_SUBSETS):
                if i != subset:
                    print >>f_bill_train[i], "%s,%s,%s" % (vote, bill_id, person_id)
                if i != vote_subset:
                    print >>f_vote_train[i], "%s,%s,%s" % (vote, bill_id, person_id)

            print >>f_vote_train["all"], "%s,%s,%s" % (vote, bill_id, person_id)

    f_bill_test.close()
    for file in f_bill_train.values():
        file.close()
    for file in f_bill_validate.values():
        file.close()
    for file in f_vote_train.values():
        file.close()
    for file in f_vote_validate.values():
        file.close()
    f_vote_test.close()

def WriteTimeSeriesVotesTrimmed(votes, bills_voted_time_series, senators_voted):
    f_vote_train_time_series = {}
    f_vote_validate_time_series = {}

    for (person_id, bill_id), (vote, date) in votes.items():
        # If we there are no votes by this senator, continue.
        if senators_voted.get(person_id, 0) == 0:
            continue

        # If there are no votes for this bill, continue.
        training_subsets, validation_subset = bills_voted_time_series.get(
            bill_id, {"voted": (None, None)})["voted"]
        if training_subsets == None and validation_subset == None:
            #print "error?" + bill_id
            continue

        if validation_subset:
            if validation_subset not in f_vote_validate_time_series:
                f_vote_validate_time_series[validation_subset] = open("%s_%s" % (OPT.votes_validate_time_series_out, validation_subset), "w")
            print >>f_vote_validate_time_series[validation_subset], (
                "%s,%s,%s" % (vote, bill_id, person_id))

        for training_subset in training_subsets:
            if training_subset not in f_vote_train_time_series:
                f_vote_train_time_series[training_subset] = open("%s_%s" % (OPT.votes_train_time_series_out, training_subset), "w")
            print >>f_vote_train_time_series[training_subset], (
                "%s,%s,%s" % (vote, bill_id, person_id))

    for file in f_vote_train_time_series.values():
        file.close()
    for file in f_vote_validate_time_series.values():
        file.close()

if __name__ == '__main__':
    # Set a fixed seed for repeatability of experiments.
    random.seed(1)
    
    votes = {}
    senators_voted = {}
    bills_voted = {}
    ReadVotes(votes, senators_voted, bills_voted)

    TrimSenators(senators_voted)

    bills_voted_time_series = {}
    #    TrimBills(votes, bills_voted, bills_voted_time_series)
    bills_voted_time_series = copy.deepcopy(bills_voted)
    TrimBillsTimeSeries(votes, bills_voted_time_series)

    #    WriteVotesTrimmed(votes, bills_voted, senators_voted)
    
    WriteTimeSeriesVotesTrimmed(votes, bills_voted_time_series, senators_voted)
