from __future__ import annotations
import copy
from pathlib import Path
from typing import TYPE_CHECKING, Any

from damask import __version__ as damask_version
from damask_parse.writers import write_geom, write_load_case, write_material
from damask_parse import write_numerics

if TYPE_CHECKING:
    from matflow.param_classes.load import LoadCase


def write_input_files(
    path: Path | str,
    volume_element: dict,
    load_case: LoadCase,
    damask_solver: dict[str, str],
    homogenization: dict,
    damask_phases: dict,
    single_crystal_parameters: dict | None,
    damask_numerics: dict | None,
    initial_conditions: dict[str, Any] | None,
):
    """
    Write all the input files to DAMASK.

    Parameters
    ----------
    path
        Path to the geometry file to write.
    volume_element
        The volume element descriptor.
    load_case
        The loading case plan.
    damask_solver
        Configuration of the solver to use.
    homogenization
        Homogenisation control.
    damask_phases
        Phase information map.
    single_crystal_parameters
        Overrides for information about single crystals in the phase information map.
    damask_numerics
        Optional dict of key-value pairs to write into the DAMASK numerics control file.
        https://damask-multiphysics.org/documentation/file_formats/numerics.html
    """
    geom_path = Path(path)
    _write_geom(geom_path, volume_element, initial_conditions=initial_conditions)
    _write_load(load_case, damask_solver)
    _write_material(
        volume_element,
        homogenization,
        damask_phases,
        single_crystal_parameters,
    )
    if damask_numerics:
        _write_numerics(damask_numerics)


def _write_geom(
    path: Path, volume_element: dict, initial_conditions: dict[str, Any] | None
):
    write_geom(
        dir_path=path.parent,
        volume_element=volume_element,
        name=path.name,
        initial_conditions=initial_conditions,
    )


def _write_load(load_case: LoadCase, damask_solver: dict[str, str]):
    path = Path("load.yaml")
    write_load_case(
        dir_path=path.parent,
        load_cases=load_case.create_damask_loading_plan(),
        solver=damask_solver,
        name=path.name,
        write_2D_arrs=(damask_version != "3.0.0-alpha3"),
    )


def _write_material(
    volume_element: dict,
    homogenization: dict,
    damask_phases: dict,
    single_crystal_parameters: dict | None,
):
    path = Path("material.yaml")
    if single_crystal_parameters is not None:
        # merge single-crystal properties into phases:
        damask_phases = copy.deepcopy(damask_phases)
        for phase_label in damask_phases.keys():
            SC_params_name = damask_phases[phase_label]["mechanical"]["plastic"].pop(
                "single_crystal_parameters", None
            )
            if SC_params_name:
                SC_params = single_crystal_parameters[SC_params_name]
                damask_phases[phase_label]["mechanical"]["plastic"].update(**SC_params)

    write_material(
        dir_path=path.parent,
        homog_schemes=homogenization,
        phases=damask_phases,
        volume_element=volume_element,
        name=path.name,
    )


def _write_numerics(damask_numerics: dict):
    path = Path("numerics.yaml")
    write_numerics(dir_path=path.parent, numerics=damask_numerics, name=path.name)
