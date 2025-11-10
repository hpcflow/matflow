import numpy as np


def initialise_markov_chains(chain_index, chain_seeds, chain_g):

    x = chain_seeds[chain_index]
    g = chain_g[chain_index]
    all_x = np.array(x)[None]
    all_g = np.array([g])
    all_accept = np.array([], dtype=bool)
    return {"x": x, "g": g, "all_x": all_x, "all_g": all_g, "all_accept": all_accept}
