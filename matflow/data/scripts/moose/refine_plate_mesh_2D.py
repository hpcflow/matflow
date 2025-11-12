def refine_plate_mesh_2D(SCF, hole_sect_nodes, plate_radial_nodes, plate_diff_nodes):
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
    }
