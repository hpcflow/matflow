from __future__ import annotations
from pathlib import Path

from damask_parse.writers import write_geom as write_geom_


def write_geom(path: Path | str, volume_element: dict):
    """Write the geometry file for a spectral DAMASK simulation.

    Parameters
    ----------
    path : str or Path
        Full path to geometry file to write.
    volume_element : dict
        Dict that represents the specification of a volume element, with keys:
            element_material_idx : ndarray of shape equal to `grid_size` of int, optional
                Determines the material to which each geometric model
                element belongs, where P is the number of elements.
            grid_size : ndarray of shape (3,) of int, optional
                Geometric model grid dimensions.
            size : list of length three, optional
                Volume element size. By default set to unit size: [1.0, 1.0, 1.0].
            origin : list of length three, optional
                Volume element origin. By default: [0, 0, 0].

    Notes
    -----
    The microstructure and texture parts are not included in the header
    of the generated file.

    """
    path_ = Path(path)  # if using as a non IFG script, `path` will be a normal input
    write_geom_(dir_path=path_.parent, volume_element=volume_element, name=path_.name)
