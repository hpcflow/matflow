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
        'neff': 'dummy',
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
        f.write(f'{1:<27}(iregime ; -1=EL , 1=VP)\n')
        f.write(f'{len(phases):<27}number of phases (nph)\n')
        f.write(' '.join(str(x) for x in phase_fractions) + '  0.0\n')

        for name, phase in phases.items():
            f.write(f'*INFORMATION ABOUT PHASE {name} \n')
            f.write(f'{phase["grain_shape_control"]}   '
                    f'{phase["fragmentation_control"]}   '
                    f'{phase["critical_aspect_ratio"]}                   grain shape contrl, fragmentn, crit aspect ratio \n')
            f.write('  '.join(str(x) for x in phase['init_ellipsoid_ratios']) + '                 initial ellipsoid ratios (dummy if ishape=4)\n')
            f.write('  '.join(str(x) for x in phase['init_ellipsoid_ori']) + '                 init Eul ang ellips axes (dummy if ishape=3,4)\n')

            f.write('* name and path of texture file (filetext)\n')
            f.write(f'{name}.tex\n')
            f.write('* name and path of single crystal file (filecrys)\n')
            f.write(f'{name}.MTS\n')
            f.write('* name and path of grain shape file (dummy if ishape=0) (fileaxes)\n')
            f.write('dummy\n')
            f.write('* name and path of diffraction file (dummy if idiff=0)\n')
            f.write('0\n')
            f.write('dummy\n')

        f.write('*PRECISION SETTINGS FOR CONVERGENCE PROCEDURES (default values)\n')
        f.write(f'{numerics["errs"]} {numerics["errd"]} {numerics["errm"]} '
                f'{numerics["errso"]}    errs,errd,errm,errso\n')
        f.write(f'{numerics["itmaxext"]} {numerics["itmaxint"]} '
                f'{numerics["itmaxso"]}     itmax:   max # of iter, external, internal and SO loops\n')
        f.write(f'{numerics["irsvar"]} {numerics["jrsini"]} '
                f'{numerics["jrsfin"]} {numerics["jrstep"]}   irsvar & jrsini,jrsinp,jrstep (dummy if irsvar=0)\n')

        f.write('*INPUT/OUTPUT SETTINGS FOR THE RUN (default is zero)\n')
        f.write(f'{control["irecover"]}              irecover:read grain states from POSTMORT.IN (1) or not (0)?\n')
        f.write(f'{control["isave"]}              isave:   write grain states in POSTMORT.OUT at step (isave)?\n')
        f.write(f'{control["icubcomp"]}              icubcomp:calculate fcc rolling components? \n')
        f.write(f'{control["nwrite"]}             nwrite (frequency of texture downloads)\n')

        f.write('*MODELING CONDITIONS FOR THE RUN\n')
        f.write(f'{control["interaction"]}   {control["neff"]}      interaction (0:FC,1:afinpe,2:secant,3:neff=xx,4:tangent,5:SO),neff \n')
        f.write(f'{control["iupdate_ori"]} {control["iupdate_shape"]} '
                f'{control["iupdate_hard"]}        iupdate: update orient, grain shape, hardening \n')
        f.write(f'{control["nneigh"]}              nneigh (0 for no neighbors, 1 for pairs, etc.)\n')
        f.write(f'{control["iflu"]}               iflu (0: do not calc, 1: calc fluctuations)\n')

        f.write('*NUMBER OF PROCESSES (Lij const; Lij variable; PCYS ;LANKFORD; rigid rotatn)\n')
        f.write(f'{len(load_case)}\n')
        f.write('*IVGVAR AND PATH/NAME OF FILE FOR EACH PROCESS\n')
        for i in range(len(load_case)):
            f.write('0\n')
            f.write(f'part_{i+1}.proc\n')
