from __future__ import annotations
from pathlib import Path
import os

from damask_parse.utils import generate_viz


def viz_damask_HDF5(
    damask_hdf5_file: Path | str,
    damask_viz: dict | list,
    VE_response: dict,
) -> None:
    # On Windows, if parallel is True (in which case DAMASK will use a multiprocessing
    # writer when saving VTK files), we get `OSError: [WinError 6] The handle is invalid`.
    parallel = False if os.name == "nt" else True
    generate_viz(
        hdf5_path=damask_hdf5_file,
        viz_spec=damask_viz,
        parsed_outs=VE_response,
        parallel=parallel,
    )
