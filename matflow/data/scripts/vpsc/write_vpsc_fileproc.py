from pathlib import Path
from copy import copy

import numpy as np

from damask_parse.utils import validate_orientations


def write_vpsc_fileproc(path, load_case):
    path = Path(path)

    for i, load_part in enumerate(load_case):

        vel_grad = load_part.get('vel_grad')
        stress = load_part.get('stress')
        # rot = load_part.get('rotation')  # maybe implement later
        total_time = load_part['total_time']
        num_increments = load_part['num_increments']
        # freq = load_part.get('dump_frequency', 1)  # maybe implement later

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

        time_increment = total_time / num_increments

        path_part = path.parent / f'part_{i+1}.proc'
        with path_part.open(mode='w') as f:

            f.write(f' {num_increments} 7 {time_increment} 298.\n')
            f.write('blank\n')
            vel_grad_mask = np.logical_not(vel_grad.mask).astype(int)
            f.write(format_tensor33(vel_grad_mask))
            f.write('blank\n')
            f.write(format_tensor33(vel_grad, fmt='.3e'))
            f.write('blank\n')
            stress_mask = np.logical_not(stress.mask).astype(int)
            f.write(format_tensor33(stress_mask, sym=True))
            f.write('blank\n')
            f.write(format_tensor33(stress, fmt='.3e', sym=True))
