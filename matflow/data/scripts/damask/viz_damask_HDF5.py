from __future__ import annotations
from pathlib import Path

from damask_parse.utils import generate_viz


def viz_damask_HDF5(
    damask_hdf5_file: Path | str,
    damask_viz: dict | list,
    VE_response: dict,
) -> None:
    generate_viz(hdf5_path=damask_hdf5_file, viz_spec=damask_viz, parsed_outs=VE_response)
