from __future__ import annotations
from pathlib import Path

from damask_parse.readers import read_HDF5_file


def process_damask_HDF5(damask_hdf5_file: Path | str, damask_post_processing: list[dict]):
    """
    Apply post-processing to DAMASK output.

    Supported operations
    --------------------
    - `add_absolute`
    - `add_calculation`
    - `add_stress_Cauchy`
    - `add_determinant`
    - `add_deviator`
    - `add_eigenvalue`
    - `add_eigenvector`
    - `add_IPF_color`
    - `add_maximum_shear`
    - `add_equivalent_Mises`
    - `add_norm`
    - `add_stress_second_Piola_Kirchhoff`
    - `add_pole`
    - `add_rotation`
    - `add_spherical`
    - `add_strain`
    - `add_stretch_tensor`
    - `add_curl`
    - `add_divergence`
    - `add_gradient`

    Parameters
    ----------
    damask_hdf5_file
        File to process.
    damask_post_processing
        List of methods to invoke on the DADF5 object. This is a list of dicts with the
        following keys:
            name : str
                The name of the DADF5 method.
            args : dict
                Parameter names and their values to pass to the DADF5 method. This
                assumes all DADF5 method parameters are of positional-or-keyword type.
            opts : dict, optional
                Additional options.
    """
    _ = read_HDF5_file(hdf5_path=damask_hdf5_file, operations=damask_post_processing)
    return None
