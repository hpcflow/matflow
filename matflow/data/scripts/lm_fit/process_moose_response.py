import numpy as np


def process_moose_response(FE_response):
    # node_coords = FE_response["node_coordinates"][0]  # at time step zero
    node_disp = FE_response["disp_"][-1]  # at final time step
    node_disp_xy_flat = node_disp[:, [0, 1]].flatten()

    # print(f"process_moose_response: {node_coords.shape=!r}")
    # print(f"process_moose_response: {node_disp.shape=!r}")
    # print(f"process_moose_response: {node_disp_xy_flat.shape=!r}")
    # print(f"process_moose_response: {node_disp_xy_flat=!r}")
    return {"system_response": node_disp_xy_flat}
