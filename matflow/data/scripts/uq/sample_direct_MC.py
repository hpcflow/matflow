import os

import numpy as np
from scipy.stats import multivariate_normal


def sample_direct_MC(dimension):
    # RNG:
    random_seed = int(os.environ["MATFLOW_RUN_RANDOM_SEED"])
    sample_idx = int(os.environ["MATFLOW_ELEMENT_IDX"])  # TODO: use repeats idx?
    task_iID = int(os.environ["MATFLOW_TASK_INSERT_ID"])
    spawn_key_str = os.environ["MATFLOW_RUN_RNG_SPAWN_KEY"]
    spawn_key = tuple(int(i) for i in spawn_key_str.split(",")) if spawn_key_str else ()
    spawn_key = tuple([*spawn_key, task_iID, sample_idx])
    rng = np.random.default_rng(np.random.SeedSequence(random_seed, spawn_key=spawn_key))

    # sample in standard normal space, variates are transformed before they are passed to
    # the performance function:
    pi = multivariate_normal(mean=np.zeros(dimension), cov=None, seed=rng)
    x = np.atleast_1d(pi.rvs())
    return {"x": x}
