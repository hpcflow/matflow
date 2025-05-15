import numpy as np
from scipy.stats import multivariate_normal


def sample_direct_MC(dimension):
    # sample in standard normal space, variates are transformed before they are passed to
    # the performance function:
    pi = multivariate_normal(mean=np.zeros(dimension), cov=None)
    x = np.atleast_1d(pi.rvs())
    return {"x": x}
