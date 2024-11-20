from __future__ import annotations
import copy

from pathlib import Path

from damask import __version__
from damask_parse.writers import write_geom as write_geom_
from damask_parse.writers import write_load_case
from damask_parse.writers import write_material as write_material_
from damask_parse import write_numerics as write_numerics_


def write_input_files(
    path,
    volume_element,
    load_case,
    damask_solver,
    homogenization,
    damask_phases,
    single_crystal_parameters,
    damask_numerics,
):
    geom_path = path
    write_geom(geom_path, volume_element)
    write_load(load_case, damask_solver)
    write_material(
        volume_element,
        homogenization,
        damask_phases,
        single_crystal_parameters,
    )
    if damask_numerics:
        write_numerics(damask_numerics)


def write_geom(path, volume_element):
    write_geom_(dir_path=path.parent, volume_element=volume_element, name=path.name)


def write_load(load_case, damask_solver):
    path = Path("load.yaml")
    load_steps = []
    for step in load_case.steps:
        dct = step.to_dict()
        dct["def_grad_aim"] = dct.pop("target_def_grad", None)
        dct["def_grad_rate"] = dct.pop("target_def_grad_rate", None)
        load_steps.append(dct)

    write_load_case(
        dir_path=path.parent,
        load_cases=load_steps,
        solver=damask_solver,
        name=path.name,
        write_2D_arrs=(__version__ != "3.0.0-alpha3"),
    )


def write_material(
    volume_element,
    homogenization,
    damask_phases,
    single_crystal_parameters,
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

    write_material_(
        dir_path=path.parent,
        homog_schemes=homogenization,
        phases=damask_phases,
        volume_element=volume_element,
        name=path.name,
    )


def write_numerics(damask_numerics):
    path = Path("numerics.yaml")
    write_numerics_(dir_path=path.parent, numerics=damask_numerics, name=path.name)
