from pathlib import Path
from copy import copy

import numpy as np

from damask_parse.utils import validate_orientations


def write_vpsc_filetext(path, orientations, phases):
    # Only working for single phase ATM
    path = Path(path)
    for name, phase in phases.items():
        path_tex = path.parent / f'{name}.tex'
        break

    # Convert orientations and get size
    orientations = validate_orientations(orientations)
    euler_angles = quat2euler(orientations['quaternions'], degrees=True,
                              P=orientations['P'])
    num_oris = euler_angles.shape[0]

    # TODO: Check unit cell alignment! What conventions does VPSC code use?
    # For hex phase check and convert unit cell alignment if necessary
    # VPSC uses x // a
    # (from code: 'c' coincident with 'z' and 'a' in the plane 'xz')
    if phase['lattice'].lower() == 'hexagonal':
        if 'unit_cell_alignment' not in orientations:
            msg = 'Orientation `unit_cell_alignment` must be specified.'
            raise ValueError(msg)

        if orientations['unit_cell_alignment'].get('y') == 'b':
            # Convert from y//b to x//a:
            euler_angles[:, 2] -= 30.
            euler_angles[euler_angles[:, 2] < 0., 2] += 360.

        elif orientations['unit_cell_alignment'].get('x') != 'a':
            msg = (f'Cannot convert from the following specified unit cell '
                   f'alignment to DAMASK-compatible unit cell alignment '
                   f'(x//a): {orientations["unit_cell_alignment"]}')
            NotImplementedError(msg)

    # Add weight column
    euler_angles = np.hstack((euler_angles, np.ones((num_oris, 1))))

    with path_tex.open(mode='w') as f:
        f.write('blank\nblank\nblank\n')
        f.write(f'B   {num_oris}\n')

        np.savetxt(f, euler_angles, fmt='%.2f')
