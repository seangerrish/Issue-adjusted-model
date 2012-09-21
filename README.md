***************************
Issue-adjusted ideal point models
***************************

This code is the result of work by 

Sean M Gerrish
sgerrish[at]cs.princeton.edu.
sean.gerrish[at]gmail.com

and

David M. Blei
blei[at]cs.princeton.edu

(C) Copyright 2012, Sean M. Gerrish
   (sgerrish [at] cs [dot] princeton [dot] edu)

It includes software corresponding to models described in the
following papers:

[1] S. Gerrish and D. Blei.  How They Vote: Issue-Adjusted Models of
    Legislative Behavior.  Annual proceAdvances in Neural Information
    Processing Systems 25. 2012.

These files are part of LEGIS.

LEGIS is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation; either version 2 of the License, or (at your
option) any later version.

LEGIS is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
USA

------------------------------------------------------------------------

A. PREREQUISITES

This software requires that the numpy and scipy python modules be
installed.

B. RUNNING

The main script for this package is infer_issue_adjustments.py. A
You can see a list of command-line options by typing

./infer_issue_adjustments.py --help

Note that this package includes a supplementary dataset of votes and
bill information.  The commands we provide reference those data files.

We provide example commands for the experiments in the file
commands.sh.  For example, the following command will infer
issue-adjusted ideal points for the 111th Senate, training on folds
1,2,3,4,5 and predicting / evaluating on fold 0. (Votes from folds
1,2,3,4,5 are in votes_filename, and votes from fold 0 are given in
votes_validate_filename.)

PYTHONPATH=""
python ./infer_issue_adjustments.py \
       --votes_filename=example_data/votes.csv \
       --votes_validate_filename=example_data/votes_validate.csv \
       --mult_filename=example_data/mult.dat \
       --gammas_filename=example_data/gammas.dat \
       --model=globalzero \
       --output_root=/tmp \
       --regularization_weight=1.0

Input files:

--mult_filename: A file containing DocId in the first column.  All
  information after the first space is ignored.  These should be in an
  order that corresponds to --gammas_filename.

--gammas_filename: A file containing "gammas" estimated with a
  variational inference implementation of LDA.  These are used to
  infer the vector theta of issue weights (which is found by taking
  each row and normalizing it so it sums to one).  Each row corresponds to
  the same row in the file --gammas_filename.

--votes_filename: A list of lawmaker-bill votes for training a model,
  with three or (optionally) four columns:

     Vote (+ or -),DocId,UserId,Chamber

  DocId should be in the format "session_xxx", where session is a
  numeric session providing

--votes_validate_filename: A list of lawmaker-bill votes for evaluating a model,
  with three or (optionally) four columns:

     Vote (+ or -),DocId,UserId,Chamber

--vote_chambers_file: (Not specified and optional.) A file containing
  information about lawmakers and bills they vote on, specificially
  the columns: XXX,Chamber (s or h),DocId (bill id),Congress,UserId
  (lawmaker id) This is important because we need to keep track of
  lawmakers who transition from the House to the Senate or vice-versa.
  If specified, this overrides the chamber specified in
  votes_filename.

Output files:

final.lawmaker_stats*.csv: lawmakers' ideal points:

  UserId,x,z0,...,z{K-1}

final.docs_stats*.csv: bills' parameters:

  DocId,Polarity,Popularity

final.votes_stats*.csv: information about training votes:

  UserId,DocId,Vote,Prediction

  Where Vote gives the actual vote, and Prediction is the estimated
  log-likelihood of a vote given the posterior mode.

final.votes_validate_stats*.csv: information about validation votes:

  UserId,DocId,Vote,Prediction

  Where Vote gives the actual vote, and Prediction is the estimated
  log-likelihood of a vote given the posterior mode.

final.run_stats*.csv: information about the model fit, including the
  number of iterations and the evidence lower bound.


C. SUPPORT and QUESTIONS

This software is provided as-is, without any warranty or support,
WHATSOEVER.  If you have any questions about running this software,
you can post your question to the topic-models mailing list at
topic-models@lists.cs.princeton.edu.  You are welcome to submit
modifications or bug-fixes of this software to the authors, although
not all submissions may be posted.
