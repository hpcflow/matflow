from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
from numpy.typing import ArrayLike

try:
    from damask import GeomGrid as grid_cls
except ImportError:
    from damask import Grid as grid_cls
from damask_parse.utils import validate_volume_element, validate_orientations

if TYPE_CHECKING:
    from matflow.param_classes.orientations import Orientations
    from matflow.param_classes.seeds import MicrostructureSeeds


def generate_volume_element_voronoi(
    microstructure_seeds: MicrostructureSeeds,
    VE_grid_size: ArrayLike,
    homog_label: str,
    orientations: Orientations | None,
    scale_morphology: ArrayLike | None,
    scale_update_size: bool,
) -> dict:
    """
    Generate a volume element by Voronoi tessellation from a provided set of seeds.

    Parameters
    ----------
    microstructure_seeds
        Seeds for the crystals in the Voronoi tessellation.
    VE_grid_size
        Volume element grid size
    homog_label
        Homogenization scheme label.
    orientations
        Orientation data for the seeds.
    scale_morphology
        How to scale the morphology.
    scale_update_size
        Whether to update the grid size based on the morphology scaling.
    """
    grid_obj = grid_cls.from_Voronoi_tessellation(
        cells=np.array(VE_grid_size),
        size=np.array(microstructure_seeds.box_size),
        seeds=np.array(microstructure_seeds.position),
        periodic=True,
    )

    if scale_morphology is not None:
        scale_morphology = np.array(scale_morphology)

        original_cells = grid_obj.cells
        new_cells = original_cells * scale_morphology
        grid_scaled = grid_obj.scale(new_cells)

        if scale_update_size:
            original_size = grid_obj.size
            new_size = original_size * scale_morphology
            grid_scaled.size = new_size

        grid_obj = grid_scaled

    # TODO: this needs some more thought.

    if orientations is None:
        orientations = microstructure_seeds.orientations
        assert orientations is not None

    # see `LatticeDirection` enum:
    align_lookup = {
        "A": "a",
        "B": "b",
        "C": "c",
        "A_STAR": "a*",
        "B_STAR": "b*",
        "C_STAR": "c*",
    }
    unit_cell_alignment = {
        "x": align_lookup[orientations.unit_cell_alignment.x.name],
        "y": align_lookup[orientations.unit_cell_alignment.y.name],
        "z": align_lookup[orientations.unit_cell_alignment.z.name],
    }
    type_lookup = {
        "QUATERNION": "quat",
        "EULER": "euler",
    }
    type_ = type_lookup[orientations.representation.type.name]
    oris = {
        "type": type_,
        "unit_cell_alignment": unit_cell_alignment,
    }

    if type_ == "quat":
        quat_order = orientations.representation.quat_order.name.lower().replace("_", "-")
        oris["quaternions"] = np.array(orientations.data)
        oris["quat_component_ordering"] = quat_order
    elif type_ == "euler":
        oris["euler_angles"] = np.array(orientations.data)
        oris["euler_degrees"] = orientations.representation.euler_is_degrees

    oris = validate_orientations(oris)

    num_grains = len(microstructure_seeds.position)
    const_phase_lab = np.array([microstructure_seeds.phase_label])[
        np.zeros(num_grains, dtype=int)
    ]

    ori_idx = np.arange(num_grains)

    volume_element = {
        "size": grid_obj.size.astype(float).tolist(),
        "grid_size": grid_obj.cells.tolist(),
        "orientations": oris,
        "element_material_idx": grid_obj.material,
        "constituent_material_idx": np.arange(num_grains),
        "constituent_material_fraction": np.ones(num_grains),
        "constituent_phase_label": const_phase_lab,
        "constituent_orientation_idx": ori_idx,
        "material_homog": np.full(num_grains, homog_label),
    }
    volume_element = validate_volume_element(volume_element)
    return {"volume_element": volume_element}
