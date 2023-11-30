from damask_parse.utils import spread_orientations


def modify_VE_spread_orientations(volume_element, phases, stddev_degrees):
    VE = spread_orientations(volume_element, phases, sigmas=stddev_degrees)
    VE["grid_size"] = tuple(int(i) for i in VE["grid_size"])
    VE["size"] = tuple(float(i) for i in VE["size"])
    return {"volume_element": VE}
