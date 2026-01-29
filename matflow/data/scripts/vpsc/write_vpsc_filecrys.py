from pathlib import Path
from copy import copy

import numpy as np

from damask_parse.utils import validate_orientations


def write_vpsc_filecrys(path, phases):
    path = Path(path)

    for name, phase in phases.items():
        if phase['lattice'].lower() == 'hexagonal':
            lattice_params = f'1. 1. {phase["c/a"]} 90. 90. 120.\n'

            c_pars = phase['mechanical']['elastic']
            # Convert to GPa
            c_pars['C_11'] = c_pars['C_11'] / 1e9
            c_pars['C_12'] = c_pars['C_12'] / 1e9
            c_pars['C_13'] = c_pars['C_13'] / 1e9
            c_pars['C_33'] = c_pars['C_33'] / 1e9
            c_pars['C_44'] = c_pars['C_44'] / 1e9

            c_pars['Z'] = 0.0
            c_pars['C_66'] = (c_pars['C_11'] - c_pars['C_12']) / 2.

            stiffness = '{C_11} {C_12} {C_13} {Z} {Z} {Z}\n'.format(**c_pars)
            stiffness += '{C_12} {C_11} {C_13} {Z} {Z} {Z}\n'.format(**c_pars)
            stiffness += '{C_13} {C_13} {C_33} {Z} {Z} {Z}\n'.format(**c_pars)
            stiffness += '{Z} {Z} {Z} {C_44} {Z} {Z}\n'.format(**c_pars)
            stiffness += '{Z} {Z} {Z} {Z} {C_44} {Z}\n'.format(**c_pars)
            stiffness += '{Z} {Z} {Z} {Z} {Z} {C_66}\n'.format(**c_pars)

        elif phase['lattice'].lower() == 'cubic':
            lattice_params = '1. 1. 1. 90. 90. 90.\n'

            c_pars = phase['mechanical']['elastic']
            # Convert to GPa
            c_pars['C_11'] = c_pars['C_11'] / 1e9
            c_pars['C_12'] = c_pars['C_12'] / 1e9
            c_pars['C_44'] = c_pars['C_44'] / 1e9

            c_pars['Z'] = 0.0
            stiffness = '{C_11} {C_12} {C_12} {Z} {Z} {Z}\n'.format(**c_pars)
            stiffness += '{C_12} {C_11} {C_12} {Z} {Z} {Z}\n'.format(**c_pars)
            stiffness += '{C_12} {C_12} {C_11} {Z} {Z} {Z}\n'.format(**c_pars)
            stiffness += '{Z} {Z} {Z} {C_44} {Z} {Z}\n'.format(**c_pars)
            stiffness += '{Z} {Z} {Z} {Z} {C_44} {Z}\n'.format(**c_pars)
            stiffness += '{Z} {Z} {Z} {Z} {Z} {C_44}\n'.format(**c_pars)

            slip_systems = ("<110>(111) SLIP\n"
                            "1  12  1   0                       modex,nsmx,isensex,itwtypex\n"
                            "1    1   -1      0    1    1     slip (n & b)\n"
                            "1    1   -1      1    0    1\n"
                            "1    1   -1      1   -1    0\n"
                            "1   -1   -1      0    1   -1\n"
                            "1   -1   -1      1    0    1\n"
                            "1   -1   -1      1    1    0\n"
                            "1   -1    1      0    1    1\n"
                            "1   -1    1      1    0   -1\n"
                            "1   -1    1      1    1    0\n"
                            "1    1    1      0    1   -1\n"
                            "1    1    1      1    0   -1\n"
                            "1    1    1      1   -1    0\n")
            plastic = phase['mechanical']['plastic']
            nrsx = plastic["nrsx"]
            tau0x = plastic["tau0x"]
            tau1x = plastic["tau1x"]
            thet0 = plastic["thet0"]
            thet1 = plastic["thet1"]
            hpfac = plastic["hpfac"]
            hlatex = plastic["hlatex"]
            parameters = (f"<111>{110} SLIP -------------------------------------------\n"
                          f"{nrsx}                           nrsx\n"
                          f"{tau0x}   {tau1x}   {thet0}   {thet1}  {hpfac}        tau0x,tau1x,thet0,thet1, hpfac\n"
                          f"{hlatex}                             hlatex(1,im),im=1,nmodes)")

        else:
            msg = ('`lattice` must be `cubic`, `hexagonal`.')
            raise ValueError(msg)

        slip_modes = phase['mechanical']['plastic'].get('slip_modes', [])
        twin_modes = phase['mechanical']['plastic'].get('twin_modes', [])
        num_sl = len(slip_modes)
        num_tw = len(twin_modes)
        num_modes = num_sl + num_tw
        constitutive_law = ("*Constitutive law\n"
                           "0      Voce=0, MTS=1\n"
                           "1      iratesens (0:rate insensitive, 1:rate sensitive)\n"
                           "50     grsze --> grain size only matters if HPfactor is non-zero\n")

        path_phase = path.parent / f'{name}.sx'
        with path_phase.open(mode='w') as f:
            f.write(f'# Material: {name}\n')
            f.write(f'{phase["lattice"].upper()}\n')
            f.write(lattice_params)
            f.write('# Elastic stiffness (GPa)\n')
            f.write(stiffness)
            f.write('# Thermal expansion coefficients (ignored)\n')
            f.write('0.0 0.0 0.0 0.0 0.0 0.0 "alfcc"\n')
            f.write('# Slip and twinning modes\n')
            f.write(f'{num_modes}\n')
            f.write(f'{num_modes}\n')
            f.write(' '.join(str(i) for i in range(1, num_modes + 1)) + '\n')
            f.write(slip_systems)
#            for i, mode in enumerate(slip_modes + twin_modes):
#                tw = i >= num_sl
#                num_sys = len(mode['planes'])
#                assert len(mode['planes']) == len(mode['directions'])
#                f.write(f'{mode["name"]}\n')
#                f.write(f'{i+1} {num_sys} {mode["n"]}')
#                if tw:
#                    f.write(' 0\n')
#                    f.write(f'{mode["twsh"]} {mode["isectw"]} '
#                            f'{mode["thres_1"]} {mode["thres_2"]}\n')
#                else:
#                    f.write(' 1\n')
#                    f.write('0. 0 0. 0.\n')
#                f.write(f'{mode["tau_0"]} {mode["tau_1"]} '
#                        f'{mode["theta_0"]} {mode["theta_1"]} '
#                        f'{mode["hpfac"]} {mode["gndfac"]}\n')
#                f.write(' '.join(str(x) for x in mode['h_latent']) + '\n')
#                for pl, dr in zip(mode['planes'], mode['directions']):
#                    f.write(' '.join(str(x) for x in pl + dr) + '\n')
            f.write(constitutive_law)
            f.write(parameters) 
