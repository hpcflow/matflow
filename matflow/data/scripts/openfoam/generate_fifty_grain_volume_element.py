from __future__ import annotations

import numpy as np
from damask_parse.utils import validate_orientations, validate_volume_element

from matflow.data.scripts.openfoam.load_fifty_grain_phase_fields import (
    load_fifty_grain_phase_fields,
)
from matflow.param_classes.orientations import Orientations


GRID_SIZE = (1, 250, 250)
VOLUME_SIZE = (0.1, 0.2, 0.2)


def generate_fifty_grain_volume_element(
    orientations: Orientations, phase_field_data: str
) -> dict:
    phase_fields = load_fifty_grain_phase_fields(phase_field_data)
    orientation_data = np.asarray(orientations.data)
    if orientation_data.shape[0] != phase_fields.shape[0]:
        raise ValueError(
            "The number of orientations must match the number of Fifty Grain phases."
        )

    align_lookup = {
        "A": "a",
        "B": "b",
        "C": "c",
        "A_STAR": "a*",
        "B_STAR": "b*",
        "C_STAR": "c*",
    }
    unit_cell_alignment = {
        axis: align_lookup[getattr(orientations.unit_cell_alignment, axis).name]
        for axis in ("x", "y", "z")
    }
    type_lookup = {"QUATERNION": "quat", "EULER": "euler"}
    orientation_type = type_lookup[orientations.representation.type.name]
    orientation_data_dict = {
        "type": orientation_type,
        "unit_cell_alignment": unit_cell_alignment,
    }
    if orientation_type == "quat":
        orientation_data_dict["quaternions"] = orientation_data
        orientation_data_dict[
            "quat_component_ordering"
        ] = orientations.representation.quat_order.name.lower().replace("_", "-")
    else:
        orientation_data_dict["euler_angles"] = orientation_data
        orientation_data_dict[
            "euler_degrees"
        ] = orientations.representation.euler_is_degrees
    orientation_data_dict = validate_orientations(orientation_data_dict)

    num_phases = phase_fields.shape[0]
    volume_element = {
        "size": list(VOLUME_SIZE),
        "grid_size": list(GRID_SIZE),
        "orientations": orientation_data_dict,
        "element_material_idx": np.argmax(phase_fields, axis=0)
        .reshape(GRID_SIZE, order="F")
        .astype(np.int32),
        "constituent_material_idx": np.arange(num_phases),
        "constituent_material_fraction": np.ones(num_phases),
        "constituent_phase_label": np.full(num_phases, "Fe-35Ni"),
        "constituent_orientation_idx": np.arange(num_phases),
        "material_homog": np.full(num_phases, "SX"),
    }
    return {"volume_element": validate_volume_element(volume_element)}
