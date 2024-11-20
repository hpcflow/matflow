from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
from damask import __version__
from damask_parse.writers import write_load_case
if TYPE_CHECKING:
    from matflow.param_classes.load import LoadCase


def write_load(path: Path | str, load_case: LoadCase, damask_solver: dict[str, str] | None) -> None:
    """Write the load file for a DAMASK simulation.

    Parameters
    ----------
    path
        Full path to load file to write.
    load_case
        The loadings to write.
    solver
        Override information about the solver to use.
    """
    path_ = Path(path)

    load_steps = []
    for step in load_case.steps:
        dct = step.to_dict()
        dct["def_grad_aim"] = dct.pop("target_def_grad", None)
        dct["def_grad_rate"] = dct.pop("target_def_grad_rate", None)
        load_steps.append(dct)

    write_load_case(
        dir_path=path_.parent,
        load_cases=load_steps,
        solver=damask_solver,
        name=path_.name,
        write_2D_arrs=(__version__ != "3.0.0-alpha3"),
    )
