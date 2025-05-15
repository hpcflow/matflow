from __future__ import annotations
from pathlib import Path
from damask_parse import write_numerics as write_numerics_


def write_numerics(path: Path | str, damask_numerics: dict):
    """Write the optional `numerics.yaml` file for a DAMASK simulation.

    Parameters
    ----------
    path : str or Path
        Full path to the numerics file to write.
    numerics : dict
        Dict of key-value pairs to write into the file.
        https://damask-multiphysics.org/documentation/file_formats/numerics.html
    """
    path_ = Path(path)
    write_numerics_(dir_path=path_.parent, numerics=damask_numerics, name=path_.name)
