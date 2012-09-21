#!/usr/bin/python
#!/usr/local/bin/python

import csv
import math
import numpy as np
import random
import scipy as sp
import scipy.optimize as sp_optimize
import scipy.linalg as sp_linalg
import sys
import traceback
from variational_lib import VariationalGaussian, PI
from variational_lib import VariationalLaplace
import variational_lib

from optparse import OptionParser

# Import and handle flags.
parser = OptionParser()
parser.add_option("--model",
                  default="variational", # ideal, variational, globalzero, offsetzero
                  type="string",
                  dest="model")
parser.add_option("--session",
                  default=None,
                  type="string",
                  dest="session")
parser.add_option("--output_root",
                  default="/tmp",
                  type="string",
                  dest="output_root")
parser.add_option("--subset",
                  default="",
                  type="string",
                  dest="subset")
parser.add_option("--mult_filename",
                  default="/tmp",
                  type="string",
                  dest="mult_filename")
parser.add_option("--votes_filename",
                  default="/tmp",
                  type="string",
                  dest="votes_filename")
parser.add_option("--vote_chambers_file",
                  default=None,
                  type="string",
                  dest="vote_chambers_file")
parser.add_option("--votes_validate_filename",
                  default=None,
                  type="string",
                  dest="votes_validate_filename")
parser.add_option("--gammas_filename",
                  default="/tmp",
                  type="string",
                  dest="gammas_filename")
parser.add_option("--chamber",
                  default=None,
                  type="string",
                  dest="chamber")
parser.add_option("--number_topics",
                  default=74,
                  type="int",
                  dest="number_topics")
parser.add_option("--ip_dimension",
                  default=1,
                  type="int",
                  dest="ip_dimension")
parser.add_option("--regularization_weight",
                  default=1.0,
                  type="float",
                  dest="regularization_weight")
parser.add_option("--fixed_variational_variance",
                  default=1,
                  type="int",
                  dest="fixed_variational_variance")
parser.add_option("--test",
                  default=0,
                  type="int",
                  dest="test")

OPT, args = parser.parse_args()


class Legislator:
    def __init__(self, id_str, id_number):
        self.id_str = id_str
        self.id_number = id_number
        self.neighbors = []

    def AddVote(self, doc_id):
        self.neighbors.append(doc_id)


class Doc:
    def __init__(self, id_str, id_number):
        self.id_str = id_str
        self.id_number = id_number
        self.neighbors = []

    def AddVote(self, user_id):
        self.neighbors.append(user_id)


class Model:
    def __init__(self, output_root, regularization_weight,
                 number_topics, subset, ip_dimension,
                 session, chamber):
        self.iteration = 0
        self.update_ideal_points = True
        self.update_lawmaker_offsets = True

        self.output_root = output_root
        self.regularization_weight = regularization_weight
        self.number_topics = number_topics
        self.legislators_map = None
        self.docs_map = None
        self.votes = {}
        self.votes_validate = {}
        self.subset = subset
        self.chamber = chamber
        self.session = session
        self.ip_dimension=ip_dimension
        self.iteration = None

        # Fixed parameters.
        self.GLOBAL_VECTOR_VARIANCE = 1.0
        self.LAWMAKER_IP_VARIANCE = 1.0
        self.DOC_PARAM_VARIANCE = 1.0

    def SampleUserDocLikelihood(self, user_id, doc_id,
                                user_ip_samples=None,
                                user_offset_samples=None,
                                global_vector_samples=None,
                                doc_polarization_samples=None,
                                doc_popularity_samples=None,
                                df=None):
        vote = self.votes.get((user_id, doc_id), None)
        if vote is None:
            vote = self.votes_validate.get((user_id, doc_id), None)

        if vote is None:
            print "Warning: could not find vote for user %s, doc %s" % (
                user_id, doc_id)
            sys.exit(1)

        user = self.legislators_map.get(user_id, None)
        doc = self.docs_map.get(doc_id, None)
        assert user is not None
        assert doc is not None

        if user_ip_samples is None:
            user_ip_samples = self.lawmaker_ips[user.id_number].Samples()

        if user_offset_samples is None:
            user_offset_samples = self.lawmaker_offsets[user.id_number].Samples()

        if doc_polarization_samples is None:
            doc_polarization_samples = self.doc_polarizations[doc.id_number].Samples()

        if doc_popularity_samples is None:
            doc_popularity_samples = self.doc_popularities[doc.id_number].Samples()

        if global_vector_samples is None:
            global_vector_samples = self.global_vector.Samples()

        e_thetas = self.e_thetas[doc.id_number, :]

        if df is not None:
            return self.UserDocLikelihoodDf(user_id, doc_id,
                                            user_ip_samples,
                                            user_offset_samples,
                                            doc_polarization_samples,
                                            doc_popularity_samples,
                                            e_thetas,
                                            global_vector_samples,
                                            vote,
                                            df=df)
        else:
            return self.UserDocLikelihood(user_id, doc_id,
                                          user_ip_samples,
                                          user_offset_samples,
                                          doc_polarization_samples,
                                          doc_popularity_samples,
                                          e_thetas,
                                          global_vector_samples,
                                          vote)

    def UserDocLikelihood(self, user_id, doc_id,
                          user_ip_samples,
                          user_offset_samples,
                          doc_polarization_samples,
                          doc_popularity_samples,
                          e_thetas,
                          global_vector_samples,
                          vote):
        if OPT.ip_dimension == 1:
            log_odds = (
                (np.sum((global_vector_samples
                         * user_ip_samples[0, :]
                         + user_offset_samples).T
                        * e_thetas, axis=1)
                 + user_ip_samples[0, :])
                * doc_polarization_samples[0, :]
                + doc_popularity_samples)

        s = log_odds > 20.0
        log_odds[s] = 20.0
        s = log_odds < -20.0
        log_odds[s] = -20.0
        
        likelihood = 0.0
            
        if vote == "+":
            likelihood += log_odds
        else:
            pass
            
        likelihood += -np.log(1.0 + np.exp(log_odds))
        
        return (log_odds, likelihood)

    def UserDocLikelihoodDf(self, user_id, doc_id,
                            user_ip_samples,
                            user_offset_samples,
                            doc_polarization_samples,
                            doc_popularity_samples,
                            e_thetas,
                            global_vector_samples,
                            vote,
                            df):
        assert False
        dlogl_df = 0.
        if df == "lawmaker_offsets":
            doc_polarization_samples.reshape(len(doc_polarization_samples[0, :]), 1)
            dlogl_df = np.outer(doc_polarization_samples[0, :], e_thetas)
            log_odds = (
                (np.sum((global_vector_samples
                         * user_ip_samples[0, :]
                         + user_offset_samples).T
                        * e_thetas, axis=1)
                 + user_ip_samples[0, :])
                * doc_polarization_samples[0, :]
                + doc_popularity_samples)

        s = log_odds > 20.0
        log_odds[s] = 20.0
        s = log_odds < -20.0
        log_odds[s] = -20.0
        
        d_likelihood = 0.0
            
        if vote == "+":
            d_likelihood += 1
        else:
            pass
            
        d_likelihood += -np.exp(log_odds) / (1.0 + np.exp(log_odds))

        return (dlogl_df.T * d_likelihood[0, :]).T
        
    def Likelihood(self):

        # Estimate the evidence lower bound on these observations.
        likelihood = 0.0

        q_likelihood_samples = self.global_vector.LogLikelihood(
            self.global_vector.Samples().T)

        p_likelihood_samples = np.sum(
            -np.square(self.global_vector.Samples()
                       / 2.0 * self.GLOBAL_VECTOR_VARIANCE)
            - 0.5 * np.log(2. * PI)
            - 0.5 * np.log(self.GLOBAL_VECTOR_VARIANCE),
            axis=0)

        for i in range(len(self.lawmaker_ips)):
            lawmaker_ip = self.lawmaker_ips[i]
            samples = lawmaker_ip.Samples()
            p_likelihood_samples += np.sum(-np.square(samples)
                                           / (2.0 * self.LAWMAKER_IP_VARIANCE)
                                           - 0.5 * np.log(2 * PI)
                                           - 0.5 * np.log(self.LAWMAKER_IP_VARIANCE),
                                           axis=0)

            q_likelihood_samples += lawmaker_ip.LogLikelihood(samples.T)

            lawmaker_offsets = self.lawmaker_offsets[i]
            samples = lawmaker_offsets.Samples()
            p_likelihood_samples += np.sum(-np.abs(samples)
                                           * self.regularization_weight
                                           + np.log(self.regularization_weight)
                                           - np.log(2.0),
                                            axis=0)
            q_likelihood_samples += lawmaker_offsets.LogLikelihood(samples.T)
        
        for doc_id, doc in self.docs_map.items():
            i = doc.id_number
            doc_polarizations = self.doc_polarizations[i]
            samples = doc_polarizations.Samples()
            p_likelihood_samples += np.sum(-np.square(samples)
                                           / (2.0 * self.DOC_PARAM_VARIANCE)
                                           - 0.5 * np.log(2 * PI)
                                           - 0.5 * np.log(self.DOC_PARAM_VARIANCE),
                                           axis=0)
            q_likelihood_samples += doc_polarizations.LogLikelihood(samples.T)

            doc_popularities = self.doc_popularities[i]
            samples = doc_popularities.Samples()
            p_likelihood_samples += np.sum(-np.square(samples)
                                           / (2.0 * self.DOC_PARAM_VARIANCE)
                                           - 0.5 * np.log(2 * PI)
                                           - 0.5 * np.log(self.DOC_PARAM_VARIANCE),
                                           axis=0)
            q_likelihood_samples += doc_popularities.LogLikelihood(samples.T)

        accuracy_correct = 0.
        accuracy_total = 1e-5 # Nonzero to avoid division by zero.
        pluses = 0.

        for i, (doc_id, doc) in enumerate(self.docs_map.items()):
            doc = self.docs_map.get(doc_id, None)
            for k, lawmaker_id in enumerate(doc.neighbors):
                key = (lawmaker_id, doc_id)
                vote = self.votes.get(key, None)
                if vote is None:
                    vote = self.votes_validate.get(key, None)
                if vote is None:
                    print user_id, doc_id
                    assert False, "Error: could not find vote."

                log_odds, vote_likelihood = self.SampleUserDocLikelihood(
                    lawmaker_id, doc_id)

                p_likelihood_samples = p_likelihood_samples + vote_likelihood

                log_odds = np.sum(log_odds > 0) > variational_lib.NUMBER_SAMPLES / 2.
                sample_correct = (log_odds == (vote == "+"))
                
                accuracy_total += 1
                if vote == "+":
                    pluses += 1

                accuracy_correct += sample_correct

        accuracy = accuracy_correct / accuracy_total
        baseline =  pluses / accuracy_total
        
        variational_approximation = np.mean(p_likelihood_samples
                                            - q_likelihood_samples)

        return (variational_approximation, accuracy, baseline)


    def Load(self, vote_chambers=None):
        # Read training votes.
        self.legislators_map = {}
        self.docs_map = {}

        print "--Reading votes"
        votes_filename = OPT.votes_filename
        votes_file = open(votes_filename, "r")
        votes_reader = csv.reader(votes_file)
        for i, row in enumerate(votes_reader):
            if OPT.test and i > 15000:
                continue
            
            try:
                vote, doc_id, user_id, tmp_chamber = None, None, None, None
                if len(row) == 4:
                    vote, doc_id, user_id, tmp_chamber = row
                elif len(row) == 3:
                    vote, doc_id, user_id = row
                else:
                    assert False, "Error. Wrong number of rows."

                if (OPT.vote_chambers_file is None
                    and OPT.chamber is not None
                    and tmp_chamber is not None
                    and len(tmp_chamber)
                    and OPT.chamber != tmp_chamber[0]):
                    continue

                session = "-1"
                parts = doc_id.split("_")
                if len(parts) > 1:
                    session = parts[0]

                if (OPT.session is not None
                    and OPT.session != "all"
                    and session != OPT.session):
                    continue

                # Only include sessions from the range 106-111.
                if (float(session) < 106 or float(session) > 111
                    and float(session) >= 0):
                    continue

                key = (user_id, doc_id)
                if vote_chambers is not None and OPT.chamber is not None:
                    chamber = vote_chambers.get(key, None)
                    if not chamber:
                        print ("Warning.  Could not find lawmaker %s, session %s."
                               % (user_id, session))
                        continue

                    if chamber != OPT.chamber:
                        continue

                if vote not in [ "+", "-" ]:
                    continue
                self.votes[key] = vote
                if user_id not in self.legislators_map:
                    self.legislators_map[user_id] = Legislator(user_id, len(self.legislators_map))
                self.legislators_map[user_id].AddVote(doc_id)

                if doc_id not in self.docs_map:
                    self.docs_map[doc_id] = Doc(doc_id, len(self.docs_map))
                self.docs_map[doc_id].AddVote(user_id)

            except:
                traceback.print_exc()

        votes_file.close()
        print "  Read %d votes, %d docs, and %d lawmakers." % (
            len(self.votes),
            len(self.docs_map),
            len(self.legislators_map))

        print "--Reading validation votes-- "
        
        if OPT.votes_validate_filename:
            votes_filename = OPT.votes_validate_filename
            votes_file = open(votes_filename, "r")
            votes_reader = csv.reader(votes_file)
            for i, row in enumerate(votes_reader):
                try:
                    vote, doc_id, user_id, tmp_chamber = None, None, None, None
                    if len(row) == 4:
                        vote, doc_id, user_id, tmp_chamber = row
                    elif len(row) == 3:
                        vote, doc_id, user_id = row
                    else:
                        assert False, "Error. Wrong number of rows."

                    if (OPT.vote_chambers_file is None
                        and OPT.chamber is not None
                        and tmp_chamber is not None
                        and len(tmp_chamber)
                        and OPT.chamber != tmp_chamber[0]):
                        continue

                    session = "-1"
                    parts = doc_id.split("_")
                    if len(parts) > 1:
                        session = parts[0]

                    if (OPT.session is not None
                        and OPT.session != "all"
                        and session != OPT.session):
                        continue

                    # Only include sessions from the range 106-111.
                    if (float(session) < 106 or float(session) > 111
                        and float(session) >= 0):
                        continue

                    key = (user_id, doc_id)
                    if vote_chambers is not None and OPT.chamber is not None:
                        chamber = vote_chambers.get(key, None)
                        if not chamber:
                            print ("Warning.  Could not find lawmaker %s, session %s."
                                   % (user_id, session))
                            continue

                        if chamber != OPT.chamber:
                            continue

                    if vote not in [ "+", "-" ]:
                        continue

                    key = (user_id, doc_id)
                    if user_id not in self.legislators_map:
                        continue

                    if doc_id not in self.docs_map:
                        continue

                    self.votes_validate[key] = vote

                except:
                    print "Failed to read validate votes."
                    traceback.print_exc()

            votes_file.close()

            print "  Read %d validation votes." % (
                len(self.votes_validate))

        # Read the bill ids and gammas simultaneously.
        print "--reading e-thetas-- "
        self.e_thetas = np.array([ [0.0] * self.number_topics ] * len(self.docs_map))
        mult_file = open(OPT.mult_filename, "r")
        gammas_file = open(OPT.gammas_filename, "r")
        doc_e_thetas = {}
        docids_split = " "
        for i, (mult_row, gamma_row) in enumerate(zip(mult_file, gammas_file)):
            doc_id = None
            if " " in mult_row:
                parts = mult_row.split(docids_split)
                doc_id = parts[ 0 ]
            else:
                parts = mult_row.split(docids_split)
                doc_id = parts[ 0 ]

            parts = gamma_row.split(" ")
            gamma_sum = 0.0
            gammas = []
            for topic_gamma in parts:
                gammas.append(float(topic_gamma))
                
            gamma_sum = sum(gammas)
            e_thetas = [ g / gamma_sum for g in gammas ]

            doc_e_thetas[doc_id] = e_thetas

        mult_empty = False
        gammas_empty = False
        try:
            mult_file.next()
        except StopIteration:
            mult_empty = True

        try:
            gammas_file.next()
        except StopIteration:
            gammas_empty = True

        mult_file.close()
        gammas_file.close()

        if not gammas_empty or not mult_empty:
            print "Gammas or mult did not complete: gamma %s; mult %s" % (str(gammas_empty), str(mult_empty))
            sys.exit(1)

        unfound_docs = []
        for doc_id, doc in self.docs_map.items():
            if doc_id not in doc_e_thetas:
                unfound_docs.append(doc_id)
                continue
            try:
                self.e_thetas[doc.id_number, ] = doc_e_thetas[doc_id]
            except:
                print "new e_thetas: ", doc_e_thetas[doc_id]
                print "e_thetas: ", self.e_thetas[doc.id_number, ]
                traceback.print_exc()
                sys.exit(1)

        if len(unfound_docs):
            print "Could not find %d docs in gammas file.  See, e.g., %s." % (
                len(unfound_docs), ",".join(unfound_docs[:5]))
            print "Removing %d docs." % len(unfound_docs)
            
        for doc_id in unfound_docs:
            doc = self.docs_map[doc_id]
            for user_id in doc.neighbors:
                del self.votes[(user_id, doc_id)]
                for i, doc_id2 in enumerate(self.legislators_map[user_id].neighbors):
                    if doc_id2 == doc_id:
                        #print self.legislators_map[user_id].neighbors
                        del self.legislators_map[user_id].neighbors[i]
                        continue
                        #print "deleting %d." % i
                        #print self.legislators_map[user_id].neighbors

                if len(self.legislators_map[user_id].neighbors) == 0:
                    del self.legislators_map[user_id]

            del self.docs_map[doc_id]
            print "doc removed."

        for i, (_, doc) in enumerate(self.docs_map.items()):
            doc.id_number = i

        for i, (_, user) in enumerate(self.legislators_map.items()):
            user.id_number = i

        # Read evaluation votes.
        print "Initializing votes."

        # Read the topics.
        self.topics = np.array([ [0.0] * OPT.number_topics ]
                                * len(self.docs_map))

        # Prepare lawmakers.
        self.lawmaker_ips = {}
        for i in range(len(self.legislators_map)):
            self.lawmaker_ips[i] = VariationalGaussian(OPT.ip_dimension)
            if OPT.fixed_variational_variance:
                self.lawmaker_ips[i]._state[1, :] = -5.
            else:
                self.lawmaker_ips[i]._state[1, :] = 0.

        self.lawmaker_offsets = {}
        for i in range(len(self.legislators_map)):
            #self.lawmaker_offsets[i] = VariationalLaplace(OPT.number_topics)
            self.lawmaker_offsets[i] = VariationalGaussian(OPT.number_topics)

            if OPT.model not in [ "variational", "globalzero" ]:
                #self.lawmaker_offsets[i]._state[0:OPT.number_topics] = 0.
                #self.lawmaker_offsets[i]._state[OPT.number_topics] = 100.
                self.lawmaker_offsets[i]._state[0, :] = 0.

            if OPT.fixed_variational_variance:
                self.lawmaker_offsets[i]._state[1, :] = -5.
            else:
                self.lawmaker_offsets[i]._state[1, :] = 0.
                
            self.lawmaker_offsets[i].GenerateSamples()

        self.doc_polarizations = {}
        for i in range(len(self.docs_map)):
            self.doc_polarizations[i] = VariationalGaussian(OPT.ip_dimension)
            if OPT.fixed_variational_variance:
                self.doc_polarizations[i]._state[1, :] = -6.

        self.doc_popularities = {}
        for i in range(len(self.docs_map)):
            self.doc_popularities[i] = VariationalGaussian(1)
            if OPT.fixed_variational_variance:
                self.doc_popularities[i]._state[1, :] = -6.

        # Prepare global parameters.
        self.global_vector = VariationalGaussian(OPT.number_topics)
        if OPT.model not in [ "variational" ]:
            self.global_vector._state[0, :] = 0.

        self.global_vector._state[1, :] = 0.
        if OPT.fixed_variational_variance:
            self.global_vector._state[1, :] = -10.
        self.global_vector.GenerateSamples()

    def Initialize(self):
        # Start out the lawmakers at random positions.
        for i in range(len(self.legislators_map)):
            self.lawmaker_ips[i]._state[0, :] += 0.1 * np.random.random(self.ip_dimension)

        # Find a doc which was controversial.
        doc_stats = {}
        for (user_id, doc_id), vote in self.votes.items():
            if doc_id not in doc_stats:
                doc_stats[doc_id] = (0.0, 0.0)
            positive, total = doc_stats[doc_id]
            doc_stats[doc_id] = (positive + (vote == "+"), total + 1.0)

        selected_doc = None
        for doc_id, (positive, total) in doc_stats.items():
            fraction = (positive + 0.5) / (total + 1.0)
            if total < 50:
                continue
            if (#OPT.session is not None
                OPT.session != "all"
                and fraction > 0.2 and fraction < 0.8):
                selected_doc = self.docs_map[doc_id]
                self.doc_polarizations[selected_doc.id_number]._state[0:] += 1.0
                break
            elif (#OPT.session is not None
                  OPT.session == "all"
                  and fraction > 0.4 and fraction < 0.6):
                selected_doc = self.docs_map[doc_id]
                self.doc_polarizations[selected_doc.id_number]._state[0:] += 1.0
                break            

        if selected_doc is not None:
            for user_id in selected_doc.neighbors:
                user = self.legislators_map.get(user_id, None)
                if not user:
                    continue

                # print "Updating user %s with vote." % user.id_str
                if vote == "+":
                    self.lawmaker_ips[user.id_number]._state[0, 0] += 0.5
                else:
                    self.lawmaker_ips[user.id_number]._state[0, 0] -= 0.5
            

    def Regenerate(self):
        # Start out the lawmakers at random positions.
        for i in range(len(self.legislators_map)):
            self.lawmaker_ips[i].GenerateSamples()
            self.lawmaker_offsets[i].GenerateSamples()

        for i in range(len(self.docs_map)):
            self.doc_polarizations[i].GenerateSamples()
            self.doc_popularities[i].GenerateSamples()

        self.global_vector.GenerateSamples()

    def Infer(self):
        last_elbo = None
        elbo = 0.0
        converged = False
        iteration = 0
        
        # Start out with 21 samples (we will increase this).
        variational_lib.NUMBER_SAMPLES = 21

        self.Regenerate()

        moving_elbo_delta = 1e2
        iterations_from_last_increase = 0.
        while ((not converged and iteration < 300)
               and not (OPT.test and iteration > 10)):
            iteration += 1
            print "Running iteration %d." % iteration
            self.iteration = iteration

            if self.update_ideal_points:
                print "-Updating docs."
                self.UpdateDocs()

            print "-Updating lawmakers."
            self.UpdateLawmakers(update_offsets=(iteration >= 3))

            if iteration >= 3 and OPT.model in [ "variational", "offsetzero" ]:
                print "  Updating global vector."
                self.UpdateGlobalVector()

            elbo, accuracy, baseline = self.Likelihood()
            if last_elbo is None:
                last_elbo = elbo - 1e4

            # Don't update the estimate of delta elbo if we just
            # increased the number of samples.
            if iterations_from_last_increase >= 1:
                moving_elbo_delta = moving_elbo_delta * 0.6 + (elbo - last_elbo) * 0.4
            last_elbo = elbo

            iterations_from_last_increase += 1
            if (moving_elbo_delta < 10
                and iteration > 20
                and iterations_from_last_increase > 5
                and variational_lib.NUMBER_SAMPLES <= 501):
                variational_lib.NUMBER_SAMPLES *= 2
                variational_lib.NUMBER_SAMPLES = int(
                    variational_lib.NUMBER_SAMPLES)
                print "--Increasing number of Monte-Carlo samples to %d." % (
                    variational_lib.NUMBER_SAMPLES)
                self.Regenerate()
                iterations_from_last_increase = 0
            elif (moving_elbo_delta < 2.
                  and variational_lib.NUMBER_SAMPLES > 501
                  and iterations_from_last_increase > 5):
                converged = True

            print ("  Elbo: %.3f.\n"
                   "  Vote-prediction accuracy: %.3f,\n"
                   "  Baseline: %.3f,\n"
                   "  Moving elbo change: %.3f" % (
                       elbo, accuracy, baseline, moving_elbo_delta))
            
            if not converged and iteration % 20 == 0:
                self.Save(iteration)
            if not converged and iteration % 6 == 0:
                stats = { "iterations": iteration,
                          "elbo": elbo,
                          }
                self.Save("most_recent", stats=stats)

        print "Inference complete."
        stats = { "iterations": iteration,
                  "elbo": elbo,
                  }
        return stats

    def Save(self, iteration, stats=None):
        file_infix = "Top%%s_IpDim%%d_weight%%.%df_subset%%s_session_%%s_chamber%%s" % max(2, int(-np.log(self.regularization_weight) / np.log(10) + 0.001))
        file_infix = file_infix % (
            self.number_topics, self.ip_dimension,
            self.regularization_weight, self.subset,
            self.session,
            self.chamber)

        # Write out the lawmakers.
        lawmakers_file = open("%s/%s.lawmaker_stats_%s.csv" % (
                self.output_root, str(iteration), file_infix), "w")
        lawmakers_writer = csv.writer(lawmakers_file)
        lawmakers_writer.writerow(
            ["UserId"]
            + [ "Ip%d" % i for i in range(self.ip_dimension) ]
            + [ "Offset%d" % i for i in range(self.number_topics) ])
        for lawmaker_id, lawmaker in self.legislators_map.items():
            lawmaker_index = lawmaker.id_number
            row = [lawmaker_id]
            row += list(self.lawmaker_ips[lawmaker_index].Means())
            row += list(self.lawmaker_offsets[lawmaker_index].Means())
            lawmakers_writer.writerow(row)
        lawmakers_file.close()

        # Write out the docs.
        docs_file = open("%s/%s.docs_stats_%s.csv" % (
                self.output_root, str(iteration), file_infix), "w")
        docs_writer = csv.writer(docs_file)
        docs_writer.writerow(
            ["DocId"]
            + [ "Polarity%d" % i for i in range(self.ip_dimension) ]
            + [ "Popularity" ])
        for doc_id, doc in self.docs_map.items():
            doc_index = doc.id_number
            row = ([doc_id]
                   + list(self.doc_polarizations[doc_index].Means())
                   + list(self.doc_popularities[doc_index].Means()))
            docs_writer.writerow(row)
        docs_file.close()

        votes_file = open("%s/%s.votes_stats_%s.csv" % (
                self.output_root, str(iteration), file_infix), "w")
        votes_writer = csv.writer(votes_file)
        votes_writer.writerow(
            [ "UserId", "DocId", "Vote", "Prediction" ])
        total_correct = 0
        total = 1e-5
        for (user_id, doc_id), vote in self.votes.items():
            vote_log_odds, vote_likelihood = model.SampleUserDocLikelihood(
                user_id, doc_id)
            row = [ user_id, doc_id, vote, np.mean(vote_log_odds) ]
            vote_log_odds = np.sum(vote_log_odds > 0) > variational_lib.NUMBER_SAMPLES / 2.
            if vote_log_odds == (vote == "+"):
                total_correct += 1
            total += 1
            votes_writer.writerow(row)
        votes_file.close()
        if total < 1:
            print "No votes found.  Accuracy is zero."
        else:
            print "In-sample accuracy: %.3f" % (float(total_correct) / total)

        if self.votes_validate:
            total_correct = 0
            total = 0
            votes_file = open("%s/%s.votes_validate_stats_%s.csv" % (
                    self.output_root, str(iteration), file_infix), "w")
            votes_writer = csv.writer(votes_file)
            votes_writer.writerow(
                [ "UserId", "DocId", "Vote", "Prediction" ])
            for (user_id, doc_id), vote in self.votes_validate.items():
                vote_log_odds, vote_likelihood = model.SampleUserDocLikelihood(
                    user_id, doc_id)
                try:
                    row = [ user_id, doc_id, vote, np.mean(vote_log_odds) ]
                except:
                    traceback.print_exc()
                    print vote_log_odds.shape
                    print user_id, doc_id
                    sys.exit(1)
                vote_log_odds = np.sum(vote_log_odds > 0) > variational_lib.NUMBER_SAMPLES / 2.
                if vote_log_odds == (vote == "+"):
                    total_correct += 1
                total += 1
                votes_writer.writerow(row)
            votes_file.close()
            print "Validation accuracy: %.3f" % (float(total_correct) / total)

        # Write out the global stats.
        if not OPT.model in [ "globalzero", "ideal" ]:
            gstats_file = open("%s/%s.global_stats_%s.csv" % (
                       self.output_root, str(iteration), file_infix), "w")
            gstats_writer = csv.writer(gstats_file)
            gstats_writer.writerow([ "Stat", "GlobalMean", "GlobalVariance" ])
            global_stats = self.global_vector
            for topic_index in range(len(global_stats.Means())):
                gstats_writer.writerow(
                       [ "Topic%d,%.5f,%.5f"
                         % (topic_index,
                            global_stats.Means()[topic_index],
                            np.exp(global_stats.LogVariances())[topic_index]) ])
            gstats_file.close()

        if stats:
            stats_file = open("%s/%s.run_stats_%s.csv" % (
                    self.output_root, str(iteration), file_infix), "w")
            print >>stats_file, "Iterations,%d" % stats["iterations"]
            print >>stats_file, "Elbo,%d" % stats["elbo"]
            stats_file.close()

    def UpdateLawmakers(self, update_offsets=True):
        for i, (lawmaker_id, lawmaker) in enumerate(self.legislators_map.items()):
            last_mean_ip = 0.0
            last_mean_offset = 0.0

            lawmaker_ip = self.lawmaker_ips[lawmaker.id_number]
            lawmaker_offset = self.lawmaker_offsets[lawmaker.id_number]

            j = 0
            moving_sd = 0
            last_ip = 0.0
            last_offsets = 0.0
            moving_ip_mean = 0.0
            moving_offset_mean = 0.0
            repeat = False
            # while not moving_sd < 0.004 or doc_passes < 1:
            for lawmaker_it in range(200):
              if self.update_lawmaker_offsets:
                  lawmaker_offset_samples = lawmaker_offset.Sample(
                      variational_lib.NUMBER_SAMPLES)
                  q_offset_log_likelihoods = lawmaker_offset.LogLikelihood(
                      lawmaker_offset_samples)
                  offset_dlogq_dtheta = lawmaker_offset.dLogQ_dx(
                      lawmaker_offset_samples)
                  offset_d2logq_dtheta2 = lawmaker_offset.d2LogQ_dx2(
                      lawmaker_offset_samples)
                  p_offset_log_likelihoods = (
                       np.sum(-np.abs(lawmaker_offset_samples)
                              * self.regularization_weight
                              + np.log(self.regularization_weight)
                              - np.log(2.0),
                              axis=1))
              else:
                  lawmaker_offset_samples = lawmaker_offset.Samples().T
                  q_offset_log_likelihoods = 0.
                  p_offset_log_likelihoods = 0.

              if self.update_ideal_points:
                  lawmaker_ip_samples = lawmaker_ip.Sample(
                      variational_lib.NUMBER_SAMPLES)
                  q_ip_log_likelihoods = lawmaker_ip.LogLikelihood(
                      lawmaker_ip_samples)
                  ip_dlogq_dtheta = lawmaker_ip.dLogQ_dx(
                      lawmaker_ip_samples)
                  ip_d2logq_dtheta2 = lawmaker_ip.d2LogQ_dx2(
                      lawmaker_ip_samples)
                  p_ip_log_likelihoods = (
                      np.sum(-np.square(lawmaker_ip_samples)
                              / (2.0 * self.LAWMAKER_IP_VARIANCE)
                             - 0.5 * np.log(2 * PI)
                             - 0.5 * np.log(self.LAWMAKER_IP_VARIANCE),
                             axis=1))

              else:
                  lawmaker_ip_samples = lawmaker_ip.Samples().T
                  q_ip_log_likelihoods = 0.
                  p_ip_log_likelihoods = 0.

              # Perform a single second-order update.
              for k, doc_id in enumerate(lawmaker.neighbors):
                 if random.random() < 0.9 / self.iteration - 0.1:
                     continue

                 _, p_log_likelihoods = (
                     model.SampleUserDocLikelihood(
                         lawmaker_id, doc_id,
                         user_ip_samples=lawmaker_ip_samples.T,
                         user_offset_samples=lawmaker_offset_samples.T))
                 p_ip_log_likelihoods = p_ip_log_likelihoods + p_log_likelihoods
                 p_offset_log_likelihoods = (p_offset_log_likelihoods
                                             + p_log_likelihoods)

              # Update ideal points if necessary.
              p_intercept = np.mean(p_ip_log_likelihoods - q_ip_log_likelihoods)
              if self.update_ideal_points:
                  q_ip_d2l_dtheta2 = (
                      (np.square(ip_dlogq_dtheta)
                       * (p_ip_log_likelihoods - p_intercept))
                      + (ip_d2logq_dtheta2
                         * (p_ip_log_likelihoods - p_intercept)))
                  q_ip_d2l_dtheta2[1, :, :] = (
                      (np.square(ip_dlogq_dtheta)
                       * (p_ip_log_likelihoods - q_ip_log_likelihoods
                          - p_intercept - 1.0))
                      + (ip_d2logq_dtheta2
                         * (p_ip_log_likelihoods - q_ip_log_likelihoods
                            - p_intercept)))[1, :, :]
                  constant = 1.
                  while np.any(np.mean(q_ip_d2l_dtheta2[0, :, :], axis=1) > 0.) and constant < 4096 * 4096:
                      repeat = True
                      break

                  q_ip_dl_dtheta = (
                      ip_dlogq_dtheta
                      * (p_ip_log_likelihoods - p_intercept))
                  q_ip_dl_dtheta[1, :, :] = (
                      ip_dlogq_dtheta
                      * (p_ip_log_likelihoods - q_ip_log_likelihoods - p_intercept))[1, :, :]

                  m = np.mean(q_ip_d2l_dtheta2, axis=2)
                  tmp = m > 0.
                  s = m > -2e-2
                  m[s] = -2e-2
                  delta = (np.mean(q_ip_dl_dtheta, axis=2) / m)
                  delta[tmp] = 0.
                  s = np.abs(delta) > 0.1
                  delta[s] = np.sign(delta[s]) * 0.1
                  if OPT.fixed_variational_variance:
                      delta[1, :] = 0.
                  lawmaker_ip._state = (lawmaker_ip._state - delta * 4. / 5.)

              # Update offsets if necessary.
              if self.update_lawmaker_offsets and self.iteration > 10:
                  p_intercept = np.mean(p_offset_log_likelihoods - q_offset_log_likelihoods)
                  q_offset_d2l_dtheta2 = (
                      (np.square(offset_dlogq_dtheta)
                       * (p_offset_log_likelihoods - p_intercept))
                      + (offset_d2logq_dtheta2
                         * (p_offset_log_likelihoods - p_intercept)))

                  q_offset_d2l_dtheta2[1, :, :] = (
                      (np.square(offset_dlogq_dtheta)
                       * (p_offset_log_likelihoods - q_offset_log_likelihoods
                          - p_intercept - 1.0))
                      + (offset_d2logq_dtheta2
                         * (p_offset_log_likelihoods - q_offset_log_likelihoods
                            - p_intercept)))[1, :, :]

                  constant = 1.
                  while np.any(np.mean(q_offset_d2l_dtheta2[0, :, :], axis=1) > 0.) and constant < 1024:
                      repeat = True
                      break

                  q_offset_dl_dtheta = (
                      offset_dlogq_dtheta
                      * (p_offset_log_likelihoods - p_intercept))
                  q_offset_dl_dtheta[1, :, :] = (
                      offset_dlogq_dtheta
                      * (p_offset_log_likelihoods - p_intercept - q_offset_log_likelihoods))[1, :, :]
                  
                  m = np.mean(q_offset_d2l_dtheta2, axis=2)
                  if np.any(m[0, :] > -1e-2):
                      offset = np.max(np.abs(m[0, :]))
                      offset_max = np.abs(np.max(m[0, :]))
                      m[0, :] = (m - offset - offset_max)[0, :]

                  if np.any(m[1, :] > -1e-2):
                      offset = np.max(np.abs(m[1, :]))
                      offset_max = np.abs(np.max(m[1, :]))
                      m[1, :] = (m - offset - offset_max)[1, :]

                  tmp = m > 0.
                  delta = (np.mean(q_offset_dl_dtheta, axis=2) / m)
                  delta[tmp] = 0.

                  s = np.abs(delta) > 0.03
                  delta[s] = np.sign(delta[s]) * 0.03

                  if OPT.fixed_variational_variance:
                      delta[1, :] = 0.

                  if True or lawmaker_it <= 1:
                      lawmaker_offset._state = (lawmaker_offset._state - delta)

                  if i % 20 == 0 and self.iteration > 1:
                      if repeat:
                          pass

              if not repeat or lawmaker_it > 0:
                  break

            lawmaker_ip.GenerateSamples()

            lawmaker_offset.GenerateSamples()


    def UpdateGlobalVector(self):
        # Update the global vector using second-order regression.
        for it in range(1):
            global_vector = self.global_vector
            samples = global_vector.Sample(variational_lib.NUMBER_SAMPLES)
            q_log_likelihoods = global_vector.LogLikelihood(samples)
            q_dlogq_dtheta = global_vector.dLogQ_dx(samples)
            q_d2logq_dtheta2 = global_vector.d2LogQ_dx2(samples)

            p_log_likelihoods = np.sum(
                -np.square(samples)
                / (2. * self.GLOBAL_VECTOR_VARIANCE)
                - 0.5 * np.log(2. * PI)
                - 0.5 * np.log(self.GLOBAL_VECTOR_VARIANCE),
                axis=1)

            for i, (doc_id, doc) in enumerate(self.docs_map.items()):
                doc = self.docs_map.get(doc_id, None)
                for k, lawmaker_id in enumerate(doc.neighbors):
                    _, vote_likelihood = self.SampleUserDocLikelihood(
                        lawmaker_id, doc_id,
                        global_vector_samples=samples.T)

                    p_log_likelihoods = p_log_likelihoods + vote_likelihood
                    
            p_offset_mean = np.mean(p_log_likelihoods - q_log_likelihoods)
            q_d2l_dtheta2 = (
                np.square(q_dlogq_dtheta)
                * (p_log_likelihoods - q_log_likelihoods - p_offset_mean - 1.)
                + q_d2logq_dtheta2
                * (p_log_likelihoods - q_log_likelihoods - p_offset_mean))
            constant = 1.
            p_offset = p_offset_mean
            while np.any(np.mean(q_d2l_dtheta2, axis=2) > 0.) and constant < 4096 * 4096:
                break

            q_dl_dtheta = (
                q_dlogq_dtheta
                * (p_log_likelihoods - q_log_likelihoods - p_offset))
            q_d2l_dtheta2 = (
                np.square(q_dlogq_dtheta)
                * (p_log_likelihoods - q_log_likelihoods - p_offset - 1.)
                + q_d2logq_dtheta2
                * (p_log_likelihoods - q_log_likelihoods - p_offset))

            m = np.mean(q_d2l_dtheta2, axis=2)
            tmp = m > 0.
            delta = (np.mean(q_dl_dtheta, axis=2) / m)
            delta[tmp] = 0.

            s2 = np.abs(delta) > 0.5
            delta[s2] = np.sign(delta[s2]) * 0.5
            if OPT.fixed_variational_variance:
                delta[1, :] = 0.
            self.global_vector._state = (
                self.global_vector._state - delta * 4. / 5.)

            self.global_vector.GenerateSamples()

    def UpdateDocs(self):
        for i, (doc_id, doc) in enumerate(self.docs_map.items()):
          doc_ip = self.doc_polarizations[doc.id_number]
          doc_popularity = self.doc_popularities[doc.id_number]

          j = 0
          lawmaker_passes = 0
          moving_variance = 10.0
          last_mean_popularity = 0.0
          last_mean_polarization = 0.0
          moving_ip_mean = 0.0
          moving_popularity_mean = 0.0

          # Perform a single, quick estimate of docs' positions.
          for doc_it in range(2):
            doc_ip_samples = doc_ip.Sample(variational_lib.NUMBER_SAMPLES)
            doc_popularity_samples = doc_popularity.Sample(variational_lib.NUMBER_SAMPLES)

            q_ip_log_likelihoods = doc_ip.LogLikelihood(
                doc_ip_samples)
            ip_dlogq_dtheta = doc_ip.dLogQ_dx(
                doc_ip_samples)
            ip_d2logq_dtheta2 = doc_ip.d2LogQ_dx2(
                doc_ip_samples)

            q_popularity_log_likelihoods = doc_popularity.LogLikelihood(
                doc_popularity_samples)
            popularity_dlogq_dtheta = doc_popularity.dLogQ_dx(
                doc_popularity_samples)
            popularity_d2logq_dtheta2 = doc_popularity.d2LogQ_dx2(
                doc_popularity_samples)

            p_ip_log_likelihoods = (-np.sum(doc_ip_samples * doc_ip_samples,
                                            axis=1) / (2. * self.DOC_PARAM_VARIANCE))
            p_popularity_log_likelihoods = (
                -np.sum(doc_popularity_samples * doc_popularity_samples,
                        axis=1) / (2. * self.DOC_PARAM_VARIANCE))

            # Perform a single second-order update.
            for k, lawmaker_id in enumerate(doc.neighbors):
                j += 1
                if random.random() < 0.9 / self.iteration - 0.1:
                    continue
                _, p_log_likelihoods = (
                    model.SampleUserDocLikelihood(
                        lawmaker_id, doc_id,
                        doc_polarization_samples=doc_ip_samples.T,
                        doc_popularity_samples=doc_popularity_samples.T))
                p_ip_log_likelihoods = p_ip_log_likelihoods + p_log_likelihoods
                p_popularity_log_likelihoods = p_popularity_log_likelihoods + p_log_likelihoods

            # First handle the ip dimensions.
            p_intercept_mean = np.mean(p_ip_log_likelihoods - q_ip_log_likelihoods)
            p_intercept = p_intercept_mean
            q_ip_d2l_dtheta2 = (
                (np.square(ip_dlogq_dtheta)
                 * (p_ip_log_likelihoods - p_intercept))
                + (ip_d2logq_dtheta2
                   * (p_ip_log_likelihoods - p_intercept)))
            q_ip_d2l_dtheta2[1, :, :] = (
                (np.square(ip_dlogq_dtheta)
                 * (p_ip_log_likelihoods - q_ip_log_likelihoods - p_intercept - 1.0))
                + (ip_d2logq_dtheta2
                   * (p_ip_log_likelihoods - q_ip_log_likelihoods - p_intercept)))[1, :, :]
            constant = 1.
            while np.any(np.mean(q_ip_d2l_dtheta2, axis=2) > 0.) and constant < 4096 * 4096:
                break
                p_intercept = p_intercept_mean + constant * (np.square(ip_dlogq_dtheta)
                                                             + ip_d2logq_dtheta2)
                constant *= 2.
                q_ip_d2l_dtheta2 = (
                    (np.square(ip_dlogq_dtheta)
                     * (p_ip_log_likelihoods - q_ip_log_likelihoods - p_intercept - 1.0))
                    + (ip_d2logq_dtheta2
                       * (p_ip_log_likelihoods - q_ip_log_likelihoods - p_intercept)))

            q_ip_dl_dtheta = (
                ip_dlogq_dtheta
                * (p_ip_log_likelihoods - p_intercept))

            q_ip_dl_dtheta[1, :, :] = (
                ip_dlogq_dtheta
                * (p_ip_log_likelihoods - q_ip_log_likelihoods - p_intercept))[1, :, :]

            m = np.mean(q_ip_d2l_dtheta2, axis=2)
            if i % 10 == 0:
                pass
            tmp = m > 0.
            s = m > -2e-3
            m[s] = -2e-3
            delta = (np.mean(q_ip_dl_dtheta, axis=2)
                     / m * 4. / 5.)
            delta[tmp] = 0.
            s = np.abs(delta) > 0.8
            delta[s] = np.sign(delta[s]) * 0.8
            if OPT.fixed_variational_variance:
                delta[1, :] = 0.
            doc_ip._state = (doc_ip._state - delta)

            # Next handle the popularity.
            p_intercept_mean = np.mean(p_popularity_log_likelihoods - q_popularity_log_likelihoods)
            p_intercept = p_intercept_mean
            q_popularity_d2l_dtheta2 = (
                (np.square(popularity_dlogq_dtheta)
                 * (p_popularity_log_likelihoods - q_popularity_log_likelihoods - p_intercept - 1.0))
                + (popularity_d2logq_dtheta2
                   * (p_popularity_log_likelihoods - q_popularity_log_likelihoods - p_intercept)))
            constant = 1.
            while np.any(np.mean(q_popularity_d2l_dtheta2, axis=2) > 0.) and constant < 4096 * 4096:
                break
                p_intercept = p_intercept_mean + constant * (np.square(popularity_dlogq_dtheta)
                                                             + popularity_d2logq_dtheta2)
                constant *= 2.
                q_popularity_d2l_dtheta2 = (
                    (np.square(popularity_dlogq_dtheta)
                     * (p_popularity_log_likelihoods - q_popularity_log_likelihoods - p_intercept - 1.0))
                    + (popularity_d2logq_dtheta2
                       * (p_popularity_log_likelihoods - q_popularity_log_likelihoods - p_intercept)))
            q_popularity_dl_dtheta = (
                popularity_dlogq_dtheta
                * (p_popularity_log_likelihoods - q_popularity_log_likelihoods - p_intercept))
            m = np.mean(q_popularity_d2l_dtheta2, axis=2)
            tmp = m > 0.
            s = m > -2e-3
            m[s] = -2e-2
            delta = (np.mean(q_popularity_dl_dtheta, axis=2)
                     / m * 4. / 5.)
            delta[tmp] = 0.0
            s = np.abs(delta) > 0.8
            delta[s] = np.sign(delta[s]) * 0.8
            if OPT.fixed_variational_variance:
                delta[1, :] = 0.
            doc_popularity._state = (doc_popularity._state - delta)

            if i % 10 == 0:
              pass
          
          doc_ip.GenerateSamples()
          doc_popularity.GenerateSamples()
        

def ReadVoteChambers():
    vote_chambers_file = open(OPT.vote_chambers_file, "r")
    vote_chambers = {}
    reader = csv.reader(vote_chambers_file)
    for row in reader:
        vote_id, chamber, bill_id, bill_session, person_id = row
        key = (person_id, bill_id)
        vote_chambers[key] = chamber

    vote_chambers_file.close()

    return vote_chambers

if __name__ == '__main__':
    assert OPT.model in [ "ideal", "variational",
                          "globalzero", "offsetzero" ], (
        "Error.  model not found: %s" % OPT.model)
    
    vote_chambers=None
    if OPT.chamber:
        print "--Reading legislators' chambers"
        vote_chambers = ReadVoteChambers()

    print "--Initializing model"
    model = Model(OPT.output_root, OPT.regularization_weight,
                  OPT.number_topics, OPT.subset, OPT.ip_dimension,
                  OPT.session, OPT.chamber)
    if OPT.model in [ "ideal", "offsetzero" ]:
        model.update_lawmaker_offsets = False

    print "--Loading model"
    model.Load(vote_chambers=vote_chambers)

    print "--Fitting model"
    stats = model.Infer()

    print "--Model complete. Saving Model"
    model.Save("final", stats=stats)
