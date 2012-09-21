#!/usr/local/bin/python
#!/usr/bin/python

import numpy as np
import numpy.random as random
import scipy.special as special

import sys
# import scipy
import time

PI = 3.141592654

import math

def Prime(upto=100):
    return filter(lambda num: (
        num %
        np.arange(2, 1 + int(math.sqrt(num)))).all(),
                  range(2, upto + 1))

#PRIME_NUMBERS = Prime(1000)
PRIME_NUMBERS = [ 2 ]
NUMBER_SAMPLES = 100
# Define a base class for variational distributions.
# Derived classes should have all of these members defined.
class VariationalDistribution:
    def __init__(self):
        assert False, "Base class cannot be instantiated."

    def Sample(self, count=1):
        assert False, "Base class cannot be instantiated."

    def Samples(self):
        """Returns a NUMBER_SAMPLES x D array of samples."""
        assert self._samples is not None, "Error. Could not find samples."
        return self._samples

    def GenerateSamples(self):
        global PRIME_NUMBERS
        #if len(PRIME_NUMBERS) < NUMBER_SAMPLES:
        #    PRIME_NUMBERS = Prime(NUMBER_SAMPLES * 3 + 1)
        self._samples = self.DependentSample(count=NUMBER_SAMPLES).T

    def Update(self, gradients, iteration):
        """Updates the vector of parameters given the gradient."""
        assert False, "Base class cannot be instantiated."

    def LogLikelihood(self, gradients, iteration):
        """Returns the variational likelihood."""
        assert False, "Base class cannot be instantiated."

    def NormalizeGradients(self, gradients):
        return np.mean(gradients, axis=2)

    def dLogQ_dx(self, x):
        """Returns a gradient vector."""
        assert False, "Base class cannot be instantiated."

    def Update(self, gradients, iteration):
        gradients_mean = self.NormalizeGradients(gradients)

        self._samples = None

        delta = gradients_mean * 20 / (iteration + 100.)**0.8
        s = np.abs(delta) > 0.3
        delta[s] = np.sign(delta[s]) * 0.3
        assert np.all(abs(delta) <= 0.3), "Error. large delta." + str(delta) + str(delta[s])
            
        self._state = self._state + delta

        return

    
class VariationalGaussian(VariationalDistribution):
    # TODO(sgerrish): maybe we should represent the Guassian with its
    # sufficient statistics instead of its mean and variance?

    def Means(self):
        return self._state[0, :]

    def LogVariances(self):
        return self._state[1, :]

    def __init__(self, dimension):
        self.dimension = dimension
        self._mean_learning_rate = 2.0
        self._variance_learning_rate = 2.0

        self._state = np.float64([ [0.0] * dimension,
                                   [np.log(4.0)] * dimension ])

        self.GenerateSamples()

        self._iteration = 0

    def Sample(self, count=1):
        return self.DependentSample(count=count)
        #return (random.randn(count, self.dimension) * np.exp(self.LogVariances() / 2.0)
        #        + self.Means())

    def DependentSample(self, count=1):
        global PRIME_NUMBERS
        assert count >= 1, "Error.  count must be at least 1."
        interval_length = 1. / count
        offset = interval_length / 2.
        samples = np.array([ [ offset + x * interval_length
                               for x in range(count) ] ] * self.dimension).T
        #uniform = random.uniform(low=-offset, high=offset,
        #                         size=count * self.dimension)
        #uniform = uniform.reshape(count, self.dimension)
        #samples = samples + uniform
        samples = np.sqrt(2) * special.erfinv(2. * samples - 1.) * np.exp(self.LogVariances() / 2.) + self.Means()
        for i in range(self.dimension):
            random.shuffle(samples[:, i])

        return samples

    def LogLikelihood(self, x):
        return np.sum((-np.square(x - self.Means())
                       / (2. * np.exp(self.LogVariances()))
                       - 0.5 * np.sqrt(2 * PI) - 0.5 * self.LogVariances()),
                      axis=1)

    def dLogQ_dx(self, x):
        mean_gradient = (x - self.Means()) / (np.exp(self.LogVariances()))
        log_variance_gradient = (
            (np.square(x - self.Means()) / np.exp(self.LogVariances()) - 1) / 2.0)

        gradients = np.array([mean_gradient.T, log_variance_gradient.T])
        return gradients

    def d2LogQ_dx2(self, x):
        d2logq_dmean2 = -np.array([[1.]] * x.shape[0]) / np.exp(self.LogVariances())
        d2logq_dlogvariance2 = (
            -np.square(x - self.Means()) / (2.0 * np.exp(self.LogVariances())))
        gradients = np.array([d2logq_dmean2.T, d2logq_dlogvariance2.T])
        return gradients

    def NormalizeGradients(self, gradients):
        gradients_mean = np.multiply(np.mean(gradients, axis=2).T,
                                     np.array([ self._mean_learning_rate,
                                                self._variance_learning_rate ])).T

        while np.any(gradients_mean[0, :] > np.exp(self.LogVariances() / 2) * 5):
            self._mean_learning_rate *= 0.9
            gradients_mean = np.multiply(np.mean(gradients, axis=2).T,
                                         np.array([ self._mean_learning_rate,
                                                    self._variance_learning_rate ])).T

        while np.any(np.abs(gradients_mean[1, :]) > 2.) and self._variance_learning_rate > 0.0001:
            self._variance_learning_rate *= 0.9
            gradients_mean = np.multiply(np.mean(gradients, axis=2).T,
                                         np.array([ self._mean_learning_rate,
                                                    self._variance_learning_rate ])).T

        if np.any(gradients_mean[0] > np.exp(self.LogVariances() / 2) * 5):
            self._mean_learning_rate *= 0.9
            gradients_mean = np.multiply(np.mean(gradients, axis=2).T,
                                         np.array([ self._mean_learning_rate,
                                                    self._variance_learning_rate ])).T
        return gradients_mean

class VariationalLaplace(VariationalDistribution):
    def __init__(self, dimension):
        self.dimension = dimension
        self._mean_learning_rate = 1
        self._lambda_learning_rate = 10.

        self._samples = None

        self._state = np.float64([0.0] * self.dimension + [0.0])

        self.GenerateSamples()

        self._iteration = 0.

    def Means(self):
        return self._state[0:self.dimension]

    def LogLambda(self):
        return self._state[self.dimension]

    def Sample(self, count=1):
        return self.DependentSample(count=count)

        samples = random.exponential(np.exp(-self.LogLambda()), count * self.dimension)
        samples = samples * np.sign(random.random(count * self.dimension) - 0.5)
        
        samples = (samples.reshape(count, self.dimension)
                   + self._state[0:self.dimension])
        return samples


    def DependentSample(self, count=1):
        # The cdf of half of the laplace is:
        # p(x | x > 0) = lambda / 2 exp(-lambda |x|)
        # int_0^t lambda exp(-lambda t) dt
        # = sign(t) [ exp(-lambda |t|) - exp(0) ] / 2.
        # = sign(t) [ exp(-lambda |t|) - 1. ] / 2.
        assert count >= 1, "Error.  count must be at least 1."

        interval_length = 2. / count
        offset = -1 + interval_length / 2.
        samples = np.array([ [ offset + x * interval_length
                               for x in range(count) ] ]* self.dimension).T
        samples = (np.sign(samples) * np.log(1. - np.abs(samples)) / np.exp(self.LogLambda()))
        samples += self.Means()

        for i in range(self.dimension):
            random.shuffle(samples[:, i])

        return samples

    def LogLikelihood(self, x):
        return np.sum(-np.exp(self.LogLambda()) * np.abs(x - self._state[0:self.dimension])
                       + self.LogLambda() - np.log(2.0),
                       axis=1)

    def dLogQ_dx(self, x):
        mean_gradient = (np.sign(x - self._state[0:self.dimension])
                         * np.exp(self.LogLambda()))
        log_lambda_gradient = np.sum(-np.abs(x - self._state[0:self.dimension])
                                      * np.exp(self.LogLambda())
                                      + 1,
                                      axis=1)
        log_lambda_gradient = log_lambda_gradient.reshape(len(log_lambda_gradient), 1)
        gradients = np.concatenate((mean_gradient, log_lambda_gradient), axis=1)
        return gradients.T

    def d2LogQ_dx2(self, x):
        # Assume a parabola around x: ax^2 + bx + c, with b=0.
        # Note that the curvature is simply 2 * a.
        # This update need not be exact; add epsilon.
        delta = np.abs(x - self._state[0:self.dimension]) + 8e-2
        a = -np.exp(self._state[self.dimension]) / 2 / delta
        d2logq_dmean2 = 2.0 * a

        d2logq_dloglambda2 = np.sum(-np.abs(x - self._state[0:self.dimension])
                                    * np.exp(self.LogLambda()),
                                    axis=1)
        d2logq_dloglambda2 = d2logq_dloglambda2.reshape(len(d2logq_dloglambda2), 1)
        gradients = np.concatenate((d2logq_dmean2, d2logq_dloglambda2), axis=1)
        return gradients.T

    def NormalizeGradients(self, gradients):
        coefficients = np.float64([self._mean_learning_rate]
                                  * self.dimension
                                  + [self._lambda_learning_rate])
        gradients_mean = np.multiply(coefficients, np.mean(gradients, axis=1))

        while np.any(gradients_mean[0:self.dimension] > 1. / np.exp(self.LogLambda() / 2) * 5):
            self._mean_learning_rate *= 0.8
            coefficients = np.float64([self._mean_learning_rate]
                                      * self.dimension
                                      + [self._lambda_learning_rate])
            gradients_mean = np.multiply(coefficients, np.mean(gradients, axis=1))
            
        while (np.abs(gradients_mean[self.dimension]) > 200.0
               and self._lambda_learning_rate > 0.0001):
            self._lambda_learning_rate *= 0.8
            coefficients = np.float64([self._mean_learning_rate]
                                      * self.dimension
                                      + [self._lambda_learning_rate])
            gradients_mean = np.multiply(coefficients, np.mean(gradients, axis=1))
            
        if np.any(gradients_mean[0:self.dimension] > 1. / np.exp(self.LogLambda() / 2) * 5):
            self._mean_learning_rate *= 0.8
            coefficients = np.float64([self._mean_learning_rate]
                                      * self.dimension
                                      + [self._lambda_learning_rate])
            gradients_mean = np.multiply(coefficients, np.mean(gradients, axis=1))

        return gradients_mean

def Test1():
    """Test that VariationalGaussian returns the correct samples."""
    last_time = time.time()

    # Add some tests.
    q = VariationalGaussian(2)

    # Draw samples and make sure they're correctly distributed.
    NUMBER_SAMPLES = 20000
    samples = q.Sample(NUMBER_SAMPLES)
    VARIANCES = np.array([ 1.0, 5.0 ])
    MEANS = np.array([ -1.0, 2.0 ])
    q._state[0, :] = MEANS
    q._state[1, :] = np.log(VARIANCES)
    samples = q.DependentSample(NUMBER_SAMPLES)
    observed_means = np.mean(samples, axis=0)
    assert np.sum(np.abs(observed_means - MEANS)) < 0.01, (
        "Error. Incorrect means: " + str(observed_means))
    observed_variances = np.mean(np.square(samples), axis=0) - np.square(observed_means)
    assert np.sum(np.abs(observed_variances - VARIANCES)) < 0.01, (
        "Error. Incorrect variances: %.3f (expected %.3f)" % (observed_variances,
                                                              (VARIANCES)))
    print "Test 1 passed. Time: ", time.time() - last_time

def Test2():
    """Test that VariationalGaussian correctly models a multivariate gaussian.."""
    def log_p(x):
        #print "log_p"
        return np.sum(-np.square(x - np.array([5.0, 4.0, 3.0, 2.0]))
                      / (2.0 * np.exp(np.array([2.0, 1.0, 1.0, 1.0])))
                      - 0.5 * np.sqrt(2 * PI) - 0.5 * np.array([2.0, 1.0, 1.0, 1.0]),
                      axis=1)
    last_time = time.time()

    objective = -100.0
    objective_increase = 10.0
    q = VariationalGaussian(4)
    moving_variance = 10.0
    last_mean = 0.
    moving_mean = 0.0
    for n in range(500):
        samples = q.Sample(100)
        q_log_likelihoods = q.LogLikelihood(samples)

        log_ps = log_p(samples)
        #print log_ps.shape
        #print q_log_likelihoods.shape
        #print q.dLogQ_dx(samples).shape
        gradients = q.dLogQ_dx(samples) * (log_ps - q_log_likelihoods)
        last_objective = objective
        objective = objective * 0.96 + np.mean(log_ps - q_log_likelihoods) * 0.04

        variance = np.mean(np.square(last_mean - q._state))
        moving_variance = moving_variance * 0.95 + variance * 0.05
        last_mean = q._state
        if type(moving_mean) == "float":
            moving_mean = q._state
        else:
            moving_mean = moving_mean * 0.95 + q._state * 0.05

        if n % 50 == 0:
            #print q.Means(), q.LogVariances()
            pass

        q.Update(gradients, n)

        objective_change = objective - last_objective
        objective_increase = objective_increase * 0.9 + objective_change * 0.1

        #print "obj increase: ", objective_increase
        if moving_variance < 0.0001:
            break

    #print "Stopped after %d iterations." % n
    assert np.all(np.abs(moving_mean[0, :]
                         - np.array([5.0, 4.0, 3.0, 2.0])) < 1e-3), (
        "Error. Incorrect mean found: " + str(moving_mean))
    assert np.all(np.abs(moving_mean[1, :]
                         - np.array([2.0, 1.0, 1.0, 1.0])) < 1e-3), (
        "Error. Incorrect variance found: " + str(moving_mean))

    print "Test 2 passed. Time: ", time.time() - last_time

def Test3():
    """Test that VariationalGaussian correctly models a Laplace."""
    last_time = time.time()
    def log_p(x):
        return -np.sum(np.abs(x - np.array([12.0, 3.0])), axis=1)

    q = VariationalGaussian(2)
    objective = -100.0
    objective_increase = 10.0
    moving_variance = 10.0
    last_mean = 0.
    moving_mean = 0.0
    for n in range(5000):
        samples = q.Sample(100)
        q_log_likelihoods = q.LogLikelihood(samples)

        log_ps = log_p(samples)

        if n % 50 == 0:
            #print q.Means(), q.LogVariances()
            pass

        #print log_ps
        #print q_log_likelihoods
        #print log_ps.shape
        #print q_log_likelihoods.shape
        #print q.dLogQ_dx(samples).shape
        gradients = q.dLogQ_dx(samples) * (log_ps - q_log_likelihoods)
        last_objective = objective
        objective = objective * 0.96 + np.mean(log_ps - q_log_likelihoods) * 0.04

        q.Update(gradients, n)

        variance = np.mean(np.square(last_mean - q.Means()))
        moving_variance = moving_variance * 0.95 + variance * 0.05
        last_mean = q.Means()
        if type(moving_mean) == "float":
            moving_mean = q.Means()
        else:
            moving_mean = moving_mean * 0.95 + q.Means() * 0.05

        if n > 4:
            objective_change = objective - last_objective
            objective_increase = objective_increase * 0.99 + objective_change * 0.01

        if n % 100 == 0:
            pass

        if moving_variance < 0.0001:
            break

    assert np.all(np.abs(moving_mean - np.array([12.0, 3.0])) < 1e-1), (
        "Error. Incorrect mean found: " + str(q.Means()))
    print "Test 3 passed. Time: ", time.time() - last_time

def Test4():
    """Test that VariationalLaplace correctly models a Laplace / Gaussian."""
    def log_p(x):
        return np.sum(-np.square(x - np.array([5.0, 4.0, 3.0, 2.0]))
                      / (2.0 * 1 * np.exp(np.array([2.0, 1.0, 1.0, 1.0])))
                      - 0.5 * np.sqrt(2 * PI) - 0.5 * (np.log(1) + np.array([2.0, 1.0, 1.0, 1.0])),
                      axis=1)
    last_time = time.time()

    objective = -100.0
    objective_increase = 10.0
    q = VariationalLaplace(4)
    moving_variance = 10.0
    last_mean = 0.
    moving_mean = 0.0 
    for n in range(20000):
        samples = q.Sample(500)
        q_log_likelihoods = q.LogLikelihood(samples)

        log_ps = log_p(samples)
        #print log_ps.shape
        #print q_log_likelihoods.shape
        #print q.dLogQ_dx(samples).shape
        gradients = q.dLogQ_dx(samples) * (log_ps - q_log_likelihoods)
        last_objective = objective
        objective = objective * 0.96 + np.mean(log_ps - q_log_likelihoods) * 0.04

        variance = np.mean(np.square(last_mean - q._state))
        moving_variance = moving_variance * 0.97 + np.sqrt(variance) * 0.03
        last_mean = q._state
        moving_mean = moving_mean * 0.97 + q._state * 0.03

        if n % 50 == 0:
            #print q.Means(), q.LogVariances()
            pass

        q.Update(gradients, n)

        objective_change = objective - last_objective
        objective_increase = objective_increase * 0.95 + objective_change * 0.05

        #print "obj increase: ", objective_increase
        if n % 1000 == 0:
            #print moving_variance
            pass
        if moving_variance < 0.005:
            break

    print "Done after %d iterations." % n
    #print "Stopped after %d iterations." % n
    assert np.all(np.abs(moving_mean[0:4]
                         - np.array([5.0, 4.0, 3.0, 2.0])) < 4e-2), (
        "Error. Incorrect mean found: " + str(moving_mean))
    #print q._state

    print "Test 4 passed. Time: ", time.time() - last_time


def Test5():
    """Test VariationalLaplace on a Laplace posterior."""
    def log_p(x):
        #print "log_p"
        return np.sum(-np.abs(x - np.array([5.0, 4.0])) * np.exp(6.0)
                       + 6.0 - np.log(2.0),
                       axis=1)
    last_time = time.time()

    objective = -100.0
    objective_increase = 10.0
    q = VariationalLaplace(2)
    moving_variance = 10.0
    last_mean = 0.
    moving_mean = 0.0
    for n in range(200000):
        samples = q.Sample(50)
        q_log_likelihoods = q.LogLikelihood(samples)

        log_ps = log_p(samples)
        #print log_ps.shape
        #print q_log_likelihoods.shape
        #print q.dLogQ_dx(samples).shape
        gradients = q.dLogQ_dx(samples) * (log_ps - q_log_likelihoods)
        last_objective = objective
        objective = objective * 0.96 + np.mean(log_ps - q_log_likelihoods) * 0.04

        variance = np.mean(np.square(last_mean - q._state))
        moving_variance = moving_variance * 0.99 + np.sqrt(variance) * 0.01
        last_mean = q._state
        if type(moving_mean) == "float":
            moving_mean = q._state
        else:
            moving_mean = moving_mean * 0.97 + q._state * 0.03

        if n % 50 == 0:
            #print q.Means(), q.LogVariances()
            pass

        q.Update(gradients, n)

        #print "obj increase: ", objective_increase
        if moving_variance < 0.000001:
            break

    print "Done after %d iterations." % n
    #print "Stopped after %d iterations." % n
    assert np.all(np.abs(moving_mean - np.array([5.0, 4.0, 6.0])) < 3e-2), (
        "Error. Incorrect mean found: " + str(moving_mean))
    #print q._state

    print "Test 5 passed. Time: ", time.time() - last_time


def Test6():
    """Test VarationalGaussian.DependentSample."""
    last_time = time.time()

    # Add some tests.
    q = VariationalGaussian(2)

    # Draw samples and make sure they're correctly distributed.
    NUMBER_SAMPLES = 3000
    VARIANCES = np.array([ 1.0, 5.0 ])
    MEANS = np.array([ -1.0, 2.0 ])
    q._state[0, :] = MEANS
    q._state[1, :] = np.log(VARIANCES)
    samples = q.DependentSample(NUMBER_SAMPLES)
    observed_means = np.mean(samples, axis=0)
    assert np.sum(np.abs(observed_means - MEANS)) < 0.01, (
        "Error. Incorrect means: " + str(observed_means))
    observed_variances = np.mean(np.square(samples), axis=0) - np.square(observed_means)
    assert np.sum(np.abs(observed_variances - VARIANCES)) < 0.01, (
        "Error. Incorrect variances: " + str(observed_variances))

    print "Test 6 passed. Time: ", time.time() - last_time


def Test7():
    """Test DependentSample for VariationalGaussian."""
    def log_p(x):
        return np.sum(-np.square(x - np.array([5.0, 4.0, 3.0, 2.0]))
                      / (2.0 * np.exp(np.array([2.0, 1.0, 1.0, 1.0])))
                      - 0.5 * np.sqrt(2 * PI) - 0.5 * np.array([2.0, 1.0, 1.0, 1.0]),
                      axis=1)
    last_time = time.time()

    objective = -100.0
    objective_increase = 10.0
    q = VariationalGaussian(4)
    moving_variance = 10.0
    last_mean = 0.
    for n in range(500):
        samples = q.DependentSample(100)
        q_log_likelihoods = q.LogLikelihood(samples)

        log_ps = log_p(samples)
        gradients = q.dLogQ_dx(samples) * (log_ps - q_log_likelihoods)
        last_objective = objective
        objective = objective * 0.96 + np.mean(log_ps - q_log_likelihoods) * 0.04

        variance = np.mean(np.square(last_mean - q._state))
        moving_variance = moving_variance * 0.95 + variance * 0.05

        last_mean = q._state

        if n % 50 == 0:
            #print q.Means(), q.LogVariances()
            pass

        q.Update(gradients, n)

        objective_change = objective - last_objective
        objective_increase = objective_increase * 0.9 + objective_change * 0.1

        #print "obj increase: ", objective_increase
        if moving_variance < 0.0001:
            break

    #print "Stopped after %d iterations." % n
    assert np.all(np.abs(q._state[0, :]
                         - np.array([5.0, 4.0, 3.0, 2.0])) < 1e-3), (
        "Error. Incorrect mean found: " + str(q._state))
    assert np.all(np.abs(q._state[1, :]
                         - np.array([2.0, 1.0, 1.0, 1.0])) < 1e-3), (
        "Error. Incorrect variance found: " + str(q._state))

    print "Test 7 passed. Time: ", time.time() - last_time


def Test8():
    """Test that VariationalGaussian with DependentSample models a Laplace."""
    last_time = time.time()
    def log_p(x):
        return -np.sum(np.abs(x - np.array([12.0, 3.0])), axis=1)

    q = VariationalGaussian(2)
    objective = -100.0
    objective_increase = 10.0
    moving_variance = 10.0
    last_mean = 0.
    number_samples = 90
    for n in range(5000):
        samples = q.DependentSample(number_samples)
        q_log_likelihoods = q.LogLikelihood(samples)

        log_ps = log_p(samples)

        if n % 50 == 0:
            pass

        gradients = q.dLogQ_dx(samples) * (log_ps - q_log_likelihoods)
        last_objective = objective
        objective = objective * 0.96 + np.mean(log_ps - q_log_likelihoods) * 0.04

        q.Update(gradients, n)

        variance = np.mean(np.square(last_mean - q.Means()))
        moving_variance = moving_variance * 0.95 + variance * 0.05
        last_mean = q.Means()

        if n > 4:
            objective_change = objective - last_objective
            objective_increase = objective_increase * 0.99 + objective_change * 0.01

        if n % 100 == 0:
            pass

        if moving_variance < 0.00003:
            if number_samples < 10000:
                number_samples *= 2
            else:
                break

    assert np.all(np.abs(q.Means() - np.array([12.0, 3.0])) < 8e-3), (
        "Error. Incorrect mean found: " + str(q.Means()))
    print "Test 8 passed in %d iterations. Time: %.3f" % (n, time.time() - last_time)


def Test9():
    """Test VarationalLaplace.DependentSample."""
    last_time = time.time()

    # Add some tests.
    q = VariationalLaplace(2)

    # Draw samples and make sure they're correctly distributed.
    NUMBER_SAMPLES = 5001
    LAMBDA = 7.
    MEANS = np.array([ -1.0, 2.0 ])
    q._state[0:2] = MEANS
    q._state[2] = np.log(LAMBDA)
    samples = q.DependentSample(NUMBER_SAMPLES)
    observed_means = np.mean(samples, axis=0)
    assert np.sum(np.abs(observed_means - MEANS)) < 0.01, (
        "Error. Incorrect means: " + str(observed_means))
    observed_variances = np.mean(np.square(samples), axis=0) - np.square(observed_means)
    print observed_variances
    assert np.sum(np.abs(observed_variances - 2. / LAMBDA**2)) < 0.01, (
        "Error. Incorrect variances: %s (expected %.3f)" % (str(observed_variances),
                                                            2. / LAMBDA**2))

    print "Test 9 passed. Time: ", time.time() - last_time


def Test11():
    print "Test11"
    q = VariationalGaussian(5)
    print q.DependentSample(50)
    print "End Test11"
    
def Test10(): 
    """Test that VariationalGaussian with DependentSample models a mixture of Gaussians."""
    last_time = time.time()
    MEANS = (np.array([5.0, 4.0, 3.0, 2.0]) + np.array([10.0, -5.0, 100.0, 20.0])) / 2.
    def log_sum(a, b):
        return a + b
    def log_p(x):
        a = np.sum(-np.square(x - np.array([5.0, 4.0, 3.0, 2.0]))
                    / (2.0 * np.exp(np.array([2.0, 1.0, 1.0, 1.0])))
                    - 0.5 * np.sqrt(2 * PI) - 0.5 * np.array([2.0, 1.0, 1.0, 1.0]),
                    axis=1)
        b = np.sum(-np.square(x - np.array([10.0, -5.0, 100.0, 20.0]))
                    / (2.0 * np.exp(np.array([20.0, 0.1, 1.0, 10.0])))
                    - 0.5 * np.sqrt(2 * PI) - 0.5 * np.array([20.0, 0.1, 1.0, 10.0]),
                    axis=1)
        return log_sum(a, b)

    q = VariationalGaussian(4)
    objective = -100.0
    objective_increase = 10.0
    moving_variance = 10.0
    last_mean = 0.
    number_samples = 50
    for n in range(5000):
        samples = q.DependentSample(number_samples)
        q_log_likelihoods = q.LogLikelihood(samples)

        log_ps = log_p(samples)
        if n % 50 == 0:
            pass

        dldx = q.dLogQ_dx(samples)
        gradients = np.mean(dldx * (log_ps - q_log_likelihoods), axis=2)

        d2ldx2 = q.d2LogQ_dx2(samples)
        hessians = np.mean(np.square(dldx) * (log_ps - q_log_likelihoods - 1)
                           + d2ldx2 * (log_ps - q_log_likelihoods - 1),
                           axis=2)
        c = 0.01
        offsets = hessians * 0.
        while np.any(hessians > 1e-5):
            which = (hessians > 1e-5)
            offsets = np.mean(np.square(dldx) + d2ldx2, axis=2) * c
            hessians = np.mean(np.square(dldx) * (log_ps - q_log_likelihoods - 1)
                               + d2ldx2 * (log_ps - q_log_likelihoods),
                               axis=2) - np.mean(np.square(dldx) + d2ldx2, axis=2) * offsets
            c *= 1.5

        last_objective = objective
        q._state = q._state - gradients / hessians
        
        objective = objective * 0.96 + np.mean(log_ps - q_log_likelihoods) * 0.04

        variance = np.mean(np.square(last_mean - q.Means()))
        moving_variance = moving_variance * 0.95 + variance * 0.05
        last_mean = q.Means()

        if n > 4:
            objective_change = objective - last_objective
            objective_increase = objective_increase * 0.99 + objective_change * 0.01

        if n % 100 == 0:
            pass

        if moving_variance < 0.05:
            if number_samples < 5000:
                number_samples *= 1.5
            else:
                break

    assert np.all(np.abs(q.Means() - MEANS) < 8e-3), (
        "Error. Incorrect mean found: " + str(q.Means()))
    print "Test 10 passed in %d iterations. Time: %.3f" % (n, time.time() - last_time)


if __name__ == '__main__':
    print "starting tests."

    #Test11()
    #sys.exit(1)

    Test6()
    Test1()
    Test9()

    Test7()
    Test8()
    #Test10()

    Test2()
    Test3()
    Test4()
    Test5()



    print "Tests passed."



