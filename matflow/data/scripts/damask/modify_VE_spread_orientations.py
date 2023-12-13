from damask_parse.utils import spread_orientations


def modify_VE_spread_orientations(volume_element, phases, stddev_degrees):
    # need to convert Zarr arrays to numpy arrays first:
    VE = volume_element
    ori_copy = VE["orientations"]
    ori_copy["quaternions"] = ori_copy["quaternions"][:]
    VE_copy = {
        "size": VE["size"],
        "grid_size": VE["grid_size"][:],
        "orientations": ori_copy,
        "element_material_idx": VE["element_material_idx"][:],
        "constituent_material_idx": VE["constituent_material_idx"][:],
        "constituent_material_fraction": VE["constituent_material_fraction"][:],
        "constituent_phase_label": VE["constituent_phase_label"][:],
        "constituent_orientation_idx": VE["constituent_orientation_idx"][:],
        "material_homog": VE["material_homog"][:],
    }
    VE = spread_orientations(
        volume_element=VE_copy, phase_names=phases, sigmas=stddev_degrees
    )
    VE["grid_size"] = tuple(int(i) for i in VE["grid_size"])
    VE["size"] = tuple(float(i) for i in VE["size"])
    return {"volume_element": VE}
