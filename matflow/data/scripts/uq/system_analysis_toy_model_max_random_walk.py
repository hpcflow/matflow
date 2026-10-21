import pprint
from typing import Optional
import numpy as np
from scipy.stats import norm
from numpy.typing import NDArray


def get_approx_y_star_random_walk(dimension, target_pf, sigma=1):
    z = norm.ppf(1 - target_pf / 2)
    return sigma * (np.sqrt(dimension) * z - 0.5826)


def model(x):
    return np.max(x, axis=-1)


def system_analysis_toy_model_max_random_walk(
    x: NDArray, dimension: int, target_pf: float
):
    """`x` is within the failure domain if the return is greater than zero."""
    x = x[:]  # convert to numpy array
    x = np.cumsum(x, axis=-1)
    y_star = get_approx_y_star_random_walk(dimension, target_pf)
    g_i = model(x) - y_star
    return {"g": g_i}
