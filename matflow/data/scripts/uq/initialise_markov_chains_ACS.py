import numpy as np


def initialise_markov_chains_ACS(
    chain_index,
    chain_seeds,
    chain_g,
    all_g,
    all_x,
    num_chains_per_update,
    all_accept,
):

    # we pass all iterations of chain_index so we can retrieve the batch index
    # TODO: ideally expose loop indices as env vars

    chain_index_latest_iter = sorted(
        chain_index.items(), key=lambda x: int(x[0].split("_")[1])
    )[-1][1]
    batch_idx = chain_index_latest_iter["loop_idx"]["proposal_update"]
    chain_index = chain_index_latest_iter["value"]

    # chain index within the level (accouting for multiple batches):
    chain_index_level = batch_idx * num_chains_per_update + chain_index

    x = chain_seeds[chain_index_level]
    g = chain_g[chain_index_level]

    if all_g is None:
        all_g = np.array([g])
        all_x = np.array(x)[None]
        all_accept = np.array([], dtype=bool)
    else:
        all_g = np.append(all_g[chain_index], np.array([g]))
        all_x = np.vstack([all_x[chain_index], np.array([x])])
        all_accept = all_accept[chain_index]

    return {"x": x, "g": g, "all_x": all_x, "all_g": all_g, "all_accept": all_accept}
