import numpy as np


def get_stress_yy_at_point(FE_response, point, time_inc):
    dist = np.linalg.norm(FE_response["node_coordinates"][0] - point, axis=1)
    closest_idx = np.argmin(dist)
    # print(f"{closest_idx=!r}")
    return FE_response["stress_y"][time_inc, closest_idx, 1]


def calculate_plate_SCF(
    FE_response, plate_width, plate_thickness, hole_diameter, plate_diff
):

    hole_node = np.array([hole_diameter / 2, 0.0, plate_thickness / 2])
    far_node = np.array(
        [plate_width / 4, plate_width / 2 + plate_diff / 4, plate_thickness / 2]
    )

    # print(f"{plate_width=!r}")
    # print(f"{plate_thickness=!r}")
    # print(f"{hole_diameter=!r}")
    # print(f"{plate_diff=!r}")
    # print(f"{hole_node=!r}")
    # print(f"{far_node=!r}")

    hole_node_stress = get_stress_yy_at_point(FE_response, hole_node, -1)
    far_node_stress = get_stress_yy_at_point(FE_response, far_node, -1)

    # print(f"{hole_node_stress=!r}")
    # print(f"{far_node_stress=!r}")

    stress_CF = (hole_node_stress / far_node_stress).item()

    # find the expected SCF, correcting for the finite width:
    width_ratio = hole_diameter / plate_width
    k_t = 3 - 3.14 * width_ratio + 3.667 * width_ratio**2 - 1.527 * width_ratio**3
    expected_SCF = k_t / (1 - width_ratio)

    # print(f"{width_ratio=!r}")
    # print(f"{k_t=!r}")
    # print(f"{expected_SCF=!r}")
    # print(f"{stress_CF=!r}")

    return {"SCF": stress_CF, "expected_SCF": expected_SCF}
