import numpy as np


def set_initial_temperature(volume_element, initial_temperature):
    """Add uniform initial_temperature as T field to initial_conditions"""

    grid_size = volume_element["grid_size"]
    t_field = np.full(grid_size, initial_temperature)

    if "initial_conditions" in volume_element:
        initial_conditions = volume_element["initial_conditions"]
    else:
        initial_conditions = {}
    initial_conditions["T"] = t_field

    return {"initial_conditions": initial_conditions}
