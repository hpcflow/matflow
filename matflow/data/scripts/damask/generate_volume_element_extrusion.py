from __future__ import annotations
from damask_parse.utils import volume_element_from_2D_microstructure


def generate_volume_element_extrusion(
    microstructure_image: dict,
    depth: int,
    image_axes: list[str],
    homog_label: str,
    phase_label: str,
    phase_label_mapping: dict[str, str],
) -> dict:
    """Extrude a 2D microstructure by a given depth to form a 3D volume element.

    Parameters
    ----------
    microstructure_image : dict
        Dict with the following keys:
            grains : ndarray or nested list of shape (N, M)
                2D map of grain indices.
            orientations : dict
                Dict with the following keys:
                    type: str, "quat"
                    quaternions : ndarray of shape (P, 4) of float
                        Array of P row four-vectors of unit quaternions.
                    unit_cell_alignment : dict
                        Alignment of the unit cell.
            scale : float, optional
            grain_phases: list of int
                Index of phase assigned to each grain
            phase_labels: list of str
                Label of each phase
    depth : int
        By how many voxels the microstructure should be extruded.
    image_axes : list
        Directions along the ndarray axes. Possible values ('x', 'y', 'z')
    homog_label : str
        Homogenization scheme label.
    phase_label : str
        Label of the phase for single phase.
    phase_label_mapping: dict
        Mapping from phase labels in the `microstructure_image` to phase
        labels for created in the VE.

    Returns
    -------
    volume_element : dict
        Dict representation of the volume element.
    """
    volume_element = volume_element_from_2D_microstructure(
        microstructure_image=microstructure_image,
        homog_label=homog_label,
        phase_label=phase_label,
        phase_label_mapping=phase_label_mapping,
        depth=depth,
        image_axes=image_axes,
    )
    volume_element["grid_size"] = tuple(int(i) for i in volume_element["grid_size"])
    volume_element["size"] = tuple(float(i) for i in volume_element["size"])
    return {"volume_element": volume_element}
