
from pathlib import Path
from copy import copy

import numpy as np

from damask_parse.utils import validate_orientations


def format_tensor33(tensor):
    return f"""{tensor[0,0]}       {tensor[0,1]}       {tensor[0,2]}
{tensor[1,0]}       {tensor[1,1]}       {tensor[1,2]}
{tensor[2,0]}       {tensor[2,1]}       {tensor[2,2]}
"""

def partial_tensor33(tensor):
    return f"""{tensor[0,0]}       {tensor[0,1]}       {tensor[0,2]}
        {tensor[1,1]}       {tensor[1,2]}
                {tensor[2,2]}
"""



def write_vpsc_fileproc(path, load_case):
    path = Path(path)

    for i, load_part in enumerate(load_case):
        vel_grad = load_part.target_vel_grad
        stress = load_part.stress
        # rot = load_part.rotation  # maybe implement later
        total_time = load_part.total_time
        num_increments = load_part.num_increments
        # freq = load_part.dump_frequency  # maybe implement later

        if vel_grad is None and stress is None:
            msg = ('Specify either `vel_grad`, `stress` or both.')
            raise ValueError(msg)

        msg = ('To use mixed boundary conditions, `{}` must be '
               'passed as a masked array.')
        if stress is None:
            # Just vel-grad

            if isinstance(vel_grad, np.ma.core.MaskedArray):
                raise ValueError(msg.format('stress'))

            vel_grad = np.ma.masked_array(vel_grad, mask=np.zeros((3, 3)))
            stress = np.ma.masked_array(np.zeros((3, 3)), np.ones((3, 3)))

        elif vel_grad is None:
            # Just stress

            if isinstance(stress, np.ma.core.MaskedArray):
                raise ValueError(msg.format('vel-grad'))

            vel_grad = np.ma.masked_array(np.zeros((3, 3)), np.ones((3, 3)))
            stress = np.ma.masked_array(stress, mask=np.zeros((3, 3)))

        else:
            # Both vel-grad and stress

            if not isinstance(vel_grad, np.ma.core.MaskedArray):
                raise ValueError(msg.format('vel_grad'))
            if not isinstance(stress, np.ma.core.MaskedArray):
                raise ValueError(msg.format('stress'))

            if np.any(vel_grad.mask == stress.mask):
                msg = ('`vel_grad` must be component-wise exclusive with '
                       '`stress`')
                raise ValueError(msg)

        vel_grad_mask = np.logical_not(vel_grad.mask).astype(int)
        stress_mask = np.logical_not(stress.mask).astype(int)

        time_increment = total_time / num_increments

        path_part = path.parent / f'part_{i+1}.proc'
        with path_part.open(mode='w') as f:
            f.write(f' {num_increments} 1 {time_increment} 298. 298. nsteps  ictrl  eqincr  temp_ini   temp_fin\n')
            f.write('* boundary conditions           iudot    |    flag for vel.grad.\n')
            f.write(format_tensor33(vel_grad_mask))
            f.write('*                               udot     |    vel.grad (first guess)\n')
            f.write(format_tensor33(vel_grad.filled(0.0)))
            f.write('*                               iscau    |    flag for Cauchy\n')
            f.write(partial_tensor33(stress_mask))
            f.write('*                               scauchy  |    Cauchy stress\n')
            f.write(partial_tensor33(stress.filled(0.0)))
