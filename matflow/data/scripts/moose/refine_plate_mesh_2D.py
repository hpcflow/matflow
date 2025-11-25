import numpy as np


def refine_plate_mesh_2D(SCF, hole_sect_nodes, plate_radial_nodes, plate_diff_nodes):

    # over all iterations:
    all_SCF = np.array(
        [SCF[k]["value"] for k in sorted(SCF, key=lambda x: int(x.split("_")[1]))]
    )
    print(f"refine_plate_mesh_2D: {all_SCF!r}")

    all_SCF_diff = np.diff(all_SCF)
    print(f"refine_plate_mesh_2D: {all_SCF_diff!r}")

    SCF_diff = all_SCF_diff[-1] if all_SCF_diff.size else 1e10
    print(f"refine_plate_mesh_2D: {SCF_diff!r}")

    scale = 1.2
    hole_sect_nodes = int(hole_sect_nodes * scale)
    plate_radial_nodes = int(plate_radial_nodes * scale)
    plate_diff_nodes = int(plate_diff_nodes * scale)

    # should be odd:
    if hole_sect_nodes % 2 == 0:
        hole_sect_nodes += 1
    if plate_diff_nodes % 2 == 0:
        plate_diff_nodes += 1

    return {
        "hole_sect_nodes": hole_sect_nodes,
        "plate_radial_nodes": plate_radial_nodes,
        "plate_diff_nodes": plate_diff_nodes,
        "SCF_diff": SCF_diff,
    }
