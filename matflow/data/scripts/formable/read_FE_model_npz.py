import numpy as np


def format_1D_masked_array(arr, fill_symbol="x"):
    "Also formats non-masked array."

    return [
        x.item() if not isinstance(x, np.ma.core.MaskedConstant) else fill_symbol
        for x in arr
    ]


def read_FE_model_npz(npz_file_path, idx):
    """
    Read loading data from a numpy .npz file and format it for use in a matflow workflow
    """
    data = np.load(npz_file_path)
    num_incs = data["num_incs"]
    inc_size = data["inc_size"]
    inc_size_final = data["inc_size_final"]
    u_sampled_split = data["u_sampled_split"]
    strain_rate = data["strain_rate"]
    i = idx

    load_cases = []
    for j in range(num_incs[i]):
        inc_size_idx = (i,) + (2,) * (len(inc_size.shape) - 1)
        if j == num_incs[i] - 1:
            # final inc
            dt = inc_size_final[inc_size_idx]
        else:
            dt = inc_size[inc_size_idx]
        dt = abs(dt) / strain_rate

        load_cases.append(
            {
                "target_def_grad": u_sampled_split[i, j],
                "total_time": dt.item(),
                "num_increments": 1,
            }
        )

    return {"load_case": {"steps": load_cases}}
