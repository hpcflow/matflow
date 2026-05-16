import numpy as np


def evaluate_monte_carlo_estimator(g):
    print(f"{g=!r}")
    g = np.asarray(g)
    is_fail = g > 0
    return {"monte_carlo_estimator": np.mean(is_fail)}
