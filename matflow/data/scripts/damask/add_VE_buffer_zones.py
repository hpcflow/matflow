from __future__ import annotations
from damask_parse.utils import add_volume_element_buffer_zones


def add_VE_buffer_zones(
    volume_element: dict,
    buffer_sizes: list[int],
    phase_ids: list[int],
    phase_labels: list[str],
    homog_label: str,
    order: list[str],
) -> dict:
    """Add buffer material regions to a volume element.

    Parameters
    ----------
    volume_element : dict
        Dict representing the volume element that can be validated via
        `validate_volume_element`.
    buffer_sizes : list of int, length 6
        Size of buffer on each face [-x, +x, -y, +y, -z, +z]
    phase_ids : list of int, length 6
        Phase of each buffer. Relative, so 1 is the first new phase and so on
    phase_labels : list of str
        Labels of the new phases
    homog_label: str
        Homogenization scheme label.
    order : list of str
        Order to add the zones in.

    Returns
    -------
    volume_element : dict
        Dict representing modified volume element.

    """
    volume_element = add_volume_element_buffer_zones(
        volume_element=volume_element,
        buffer_sizes=buffer_sizes,
        phase_ids=phase_ids,
        phase_labels=phase_labels,
        homog_label=homog_label,
        order=order,
    )
    volume_element["grid_size"] = tuple(int(i) for i in volume_element["grid_size"])
    volume_element["size"] = tuple(float(i) for i in volume_element["size"])
    return {"volume_element": volume_element}
