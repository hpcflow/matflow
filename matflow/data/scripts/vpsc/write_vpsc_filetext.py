import numpy as np

from pathlib import Path
from copy import copy
from damask_parse.utils import validate_orientations
from numpy.typing import NDArray
from matflow.param_classes.orientations import Orientations

def write_vpsc_filetext(path, orientations, phases):
    # Only working for single phase ATM
    path = Path(path)
    for name, phase in phases.items():
        path_tex = path.parent / f'{name}.tex'
        break

    # Convert orientations and get size
    orientations = _convert_orientations_to_old_matflow_format(orientations)
    orientations = validate_orientations(orientations)
    euler_angles = _quat2euler(orientations['quaternions'], degrees=True,
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


def _convert_orientations_to_old_matflow_format(orientations: Orientations):
    # see `LatticeDirection` enum:
    align_lookup = {
        "A": "a",
        "B": "b",
        "C": "c",
        "A_STAR": "a*",
        "B_STAR": "b*",
        "C_STAR": "c*",
    }
    unit_cell_alignment = {
        "x": align_lookup[orientations.unit_cell_alignment.x.name],
        "y": align_lookup[orientations.unit_cell_alignment.y.name],
        "z": align_lookup[orientations.unit_cell_alignment.z.name],
    }
    type_lookup = {
        "QUATERNION": "quat",
        "EULER": "euler",
    }
    type_ = type_lookup[orientations.representation.type.name]
    oris = {
        "type": type_,
        "unit_cell_alignment": unit_cell_alignment,
    }

    if type_ == "quat":
        quat_order = orientations.representation.quat_order.name.lower().replace("_", "-")
        oris["quaternions"] = np.array(orientations.data)
        oris["quat_component_ordering"] = quat_order
    elif type_ == "euler":
        oris["euler_angles"] = np.array(orientations.data)
        oris["euler_degrees"] = orientations.representation.euler_is_degrees

    return oris

# This next function is from matflow.matflow_dream3d.utilities
# https://github.com/LightForm-group/matflow-dream3d/blob/3c73bd043b8e80bdc17af434e9e89a1660cffc2d/matflow_dream3d/utilities.py
def _quat2euler(quats: NDArray, degrees: bool = False, P: int = 1) -> NDArray:
    """Convert quaternions to Bunge-convention Euler angles.

    Parameters
    ----------
    quats : ndarray of shape (N, 4) of float
        Array of N row four-vectors of unit quaternions.
    degrees : bool, optional
        If True, `euler_angles` are returned in degrees, rather than radians.

    P : int, optional
        The "P" constant, either +1 or -1, as defined within [1].

    Returns
    -------
    euler_angles : ndarray of shape (N, 3) of float
        Array of N row three-vectors of Euler angles, specified as proper Euler angles in
        the Bunge convention (rotations are about Z, new X, new new Z).

    Notes
    -----
    Conversion of quaternions to Bunge Euler angles due to Ref. [1].

    References
    ----------
    [1] Rowenhorst, D, A D Rollett, G S Rohrer, M Groeber, M Jackson,
        P J Konijnenberg, and M De Graef. "Consistent Representations
        of and Conversions between 3D Rotations". Modelling and Simulation
        in Materials Science and Engineering 23, no. 8 (1 December 2015):
        083501. https://doi.org/10.1088/0965-0393/23/8/083501.

    """

    num_oris = quats.shape[0]
    euler_angles = np.zeros((num_oris, 3))

    q0, q1, q2, q3 = quats.T

    q03 = q0**2 + q3**2
    q12 = q1**2 + q2**2
    chi = np.sqrt(q03 * q12)

    chi_zero_idx = np.isclose(chi, 0)
    q12_zero_idx = np.isclose(q12, 0)
    q03_zero_idx = np.isclose(q03, 0)

    # Three cases are distinguished:
    idx_A = np.logical_and(chi_zero_idx, q12_zero_idx)
    idx_B = np.logical_and(chi_zero_idx, q03_zero_idx)
    idx_C = np.logical_not(chi_zero_idx)

    q0A, q3A = q0[idx_A], q3[idx_A]
    q1B, q2B = q1[idx_B], q2[idx_B]
    q0C, q1C, q2C, q3C, chiC = q0[idx_C], q1[idx_C], q2[idx_C], q3[idx_C], chi[idx_C]

    q03C = q03[idx_C]
    q12C = q12[idx_C]

    # Case 1
    euler_angles[idx_A, 0] = np.arctan2(-2 * P * q0A * q3A, q0A**2 - q3A**2)

    # Case 2
    euler_angles[idx_B, 0] = np.arctan2(2 * q1B * q2B, q1B**2 - q2B**2)
    euler_angles[idx_B, 1] = np.pi

    # Case 3
    euler_angles[idx_C, 0] = np.arctan2(
        (q1C * q3C - P * q0C * q2C) / chiC,
        (-P * q0C * q1C - q2C * q3C) / chiC,
    )
    euler_angles[idx_C, 1] = np.arctan2(2 * chiC, q03C - q12C)
    euler_angles[idx_C, 2] = np.arctan2(
        (P * q0C * q2C + q1C * q3C) / chiC,
        (q2C * q3C - P * q0C * q1C) / chiC,
    )

    euler_angles[euler_angles[:, 0] < 0, 0] += 2 * np.pi
    euler_angles[euler_angles[:, 2] < 0, 2] += 2 * np.pi

    if degrees:
        euler_angles = np.rad2deg(euler_angles)

    return euler_angles

