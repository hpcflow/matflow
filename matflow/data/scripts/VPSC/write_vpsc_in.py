from pathlib import Path
from copy import copy

import numpy as np

from damask_parse.utils import validate_orientations


def write_vpsc_in(path, control, phases, load_case, numerics):
    numerics_defaults = {
        'errs': 0.001,
        'errd': 0.001,
        'errm': 0.001,
        'errso': 0.001,

        'itmaxext': 100,
        'itmaxint': 25,
        'itmaxso': 25,

        'irsvar': 0,
        'jrsini': 2,
        'jrsfin': 10,
        'jrstep': 2,

        'ibcinv': 1,
    }
    control_defaults = {
        'irecover': 0,
        'isave': 0,
        'icubcomp': 0,
        'nwrite': 0,

        'ihardlaw': 0,
        'iratesens': 1,
        'interaction': 1,
        'iupdate_ori': 1,
        'iupdate_shape': 1,
        'iupdate_hard': 1,
        'nneigh': 0,
        'iflu': 0,
    }
    phase_defaults = {
        'fraction': 1.0,
        'grain_shape_control': 0,
        'fragmentation_control': 0,
        'critical_aspect_ratio': 25,
        'init_ellipsoid_ratios': [1.0, 1.0, 1.0],
        'init_ellipsoid_ori': [0.0, 0.0, 0.0],
    }

    if numerics is not None:
        numerics_defaults.update(numerics)
    numerics = numerics_defaults
    if control is not None:
        control_defaults.update(control)
    control = control_defaults
    phases_defaults = {}
    for name, phase in phases.items():
        phase_d = copy(phase_defaults)
        phase_d.update(phase)
        phases_defaults[name] = phase_d
    phases = phases_defaults

    phase_fractions = [phase['fraction'] for phase in phases.values()]
    assert(sum(phase_fractions) == 1.0)

    path = Path(path)
    with path.open(mode='w') as f:
        f.write('1 \n')
        f.write(f'{len(phases)}\n')
        f.write(' '.join(str(x) for x in phase_fractions) + '\n')

        for name, phase in phases.items():
            f.write(f'# Info on phase `{name}`\n')
            f.write(f'{phase["grain_shape_control"]} '
                    f'{phase["fragmentation_control"]} '
                    f'{phase["critical_aspect_ratio"]}\n')
            f.write(' '.join(str(x) for x in phase['init_ellipsoid_ratios']) + '\n')
            f.write(' '.join(str(x) for x in phase['init_ellipsoid_ori']) + '\n')

            f.write('blank\n')
            f.write(f'{name}.tex\n')
            f.write('blank\n')
            f.write(f'{name}.sx\n')
            f.write('blank\n')
            f.write('blank\n')

        f.write('# Convergence paramenters\n')
        f.write(f'{numerics["errs"]} {numerics["errd"]} {numerics["errm"]} '
                f'{numerics["errso"]}\n')
        f.write(f'{numerics["itmaxext"]} {numerics["itmaxint"]} '
                f'{numerics["itmaxso"]}\n')
        f.write(f'{numerics["irsvar"]} {numerics["jrsini"]} '
                f'{numerics["jrsfin"]} {numerics["jrstep"]}\n')
        f.write(f'{numerics["ibcinv"]}\n')

        f.write('# IO paramenters\n')
        f.write(f'{control["irecover"]}\n')
        f.write(f'{control["isave"]}\n')
        f.write(f'{control["icubcomp"]}\n')
        f.write(f'{control["nwrite"]}\n')

        f.write('# Model paramenters\n')
        f.write(f'{control["ihardlaw"]}\n')
        f.write(f'{control["iratesens"]}\n')
        f.write(f'{control["interaction"]}\n')
        f.write(f'{control["iupdate_ori"]} {control["iupdate_shape"]} '
                f'{control["iupdate_hard"]}\n')
        f.write(f'{control["nneigh"]}\n')
        f.write(f'{control["iflu"]}\n')

        f.write('# Process paramenters\n')
        f.write(f'{len(load_case)}\n')
        f.write('blank\n')
        for i in range(len(load_case)):
            f.write('0\n')
            f.write(f'part_{i+1}.proc\n')
