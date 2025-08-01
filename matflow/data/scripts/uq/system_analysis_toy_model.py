import pprint
from typing import Optional
import numpy as np
from scipy.stats import norm
from numpy.typing import NDArray


def model(x):
    return np.sum(x)


def get_y_star(p_f, dimension):
    return np.sqrt(dimension) * norm.ppf(1 - p_f)


def system_analysis_toy_model(x: NDArray, dimension: int, target_pf: float):
    """`x` is within the failure domain if the return is greater than zero."""
    x = x[:]  # convert to numpy array
    y_star = get_y_star(target_pf, dimension)
    g_i = model(x) - y_star
    return {"g": g_i}
