import numpy as np
from scipy.stats import norm


def get_y_star_normal(p_f, dimension):
    return np.sqrt(dimension) * norm.ppf(1 - p_f)


def evaluate_limit_state_normal_sum(x, sum_y, target_pf, dimension):
    y_star = get_y_star_normal(target_pf, dimension)
    return {"g": sum_y - y_star}
