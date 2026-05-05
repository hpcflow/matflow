from __future__ import annotations
from pathlib import Path

import numpy as np


def dump_all_yield_stresses(
    VE_response: list[dict], yield_point: float, dump_path: str | Path
) -> dict:
    all_VE_responses = VE_response
    yield_stresses = []
    for VE_resp_i in all_VE_responses:
        strain = VE_resp_i["phase_data"]["vol_avg_equivalent_plastic_strain"]["data"][:]
        yield_idx = np.argmin(np.abs(strain - yield_point))
        stress_i = VE_resp_i["phase_data"]["vol_avg_equivalent_stress"]["data"][yield_idx]
        yield_stresses.append(stress_i)

    with Path(dump_path).open("wt") as fh:
        for i in yield_stresses:
            fh.write(f"{i:.5f}\n")
    return {}
