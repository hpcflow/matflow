import numpy as np


def get_reference_data_moose(FE_response):
    node_coords = FE_response["node_coordinates"][0]  # at time step zero
    node_disp = FE_response["disp_"][-1]  # at final time step
    node_disp_xy_flat = node_disp[:, [0, 1]].flatten()

    # print(f"get_reference_data_moose: {node_coords.shape=!r}")
    # print(f"get_reference_data_moose: {node_disp.shape=!r}")
    # print(f"get_reference_data_moose: {node_disp_xy_flat.shape=!r}")
    # print(f"get_reference_data_moose: {node_disp_xy_flat=!r}")
    return {"x": node_coords, "reference_response": node_disp_xy_flat}
