import numpy as np


def evaluate_ML_monte_carlo_level_estimator(x, VE_grid_size, g):
    """
    VE_grid_size
        Provided to associate the values of g with their grid sizes.
    """

    print(f"{[i[:] for i in x]=!r}")
    print(f"{VE_grid_size=!r}")
    print(f"{g=!r}")

    g = np.asarray(g)
    is_fail = g > 0
    if len(set(tuple(i) for i in VE_grid_size)) == 1:
        # initial, single term
        indicator = is_fail
    else:
        # level > 0 term, need to find the difference between levels
        indicator = is_fail[::2].astype(int) - is_fail[1::2].astype(int)

    print(f"{indicator=!r}")
    print(f"{np.mean(indicator)=!r}")
    return {"mean_indicator": np.mean(indicator)}
