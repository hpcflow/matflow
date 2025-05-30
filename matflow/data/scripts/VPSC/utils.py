import numpy as np


def quat2euler(quats, degrees=False, P=1):
    """Convert unit quaternions to Bunge-convention Euler angles.

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
        Array of N row three-vectors of Euler angles, specified as proper
        Euler angles in the Bunge convention (rotations are about Z, new X,
        new new Z).

    Notes
    -----
    Conversion of Bunge Euler angles to quaternions due to Ref. [1].

    References
    ----------
    [1] Rowenhorst, D, A D Rollett, G S Rohrer, M Groeber, M Jackson,
        P J Konijnenberg, and M De Graef. "Consistent Representations
        of and Conversions between 3D Rotations". Modelling and Simulation
        in Materials Science and Engineering 23, no. 8 (1 December 2015):
        083501. https://doi.org/10.1088/0965-0393/23/8/083501.

    """
    if P not in [-1, 1]:
        raise ValueError('P must be -1 or +1')

    q03 = quats[:, 0]**2 + quats[:, 3]**2
    q12 = quats[:, 1]**2 + quats[:, 2]**2
    chi = np.sqrt(q03 * q12)

    euler_angles = np.zeros_like(quats, shape=(quats.shape[0], 3))

    # Case 1 chi = 0 and q12 = 0
    cond1 = q12 < 1e-8

    cos_ph1 = quats[cond1, 0]**2 - quats[cond1, 3]**2
    sin_ph1 = -2 * P * quats[cond1, 0] * quats[cond1, 3]

    euler_angles[cond1, 0] = np.arctan2(sin_ph1, cos_ph1)

    # Case 2 chi = 0 and q03 = 0
    cond2 = q03 < 1e-8

    cos_ph1 = quats[cond2, 1]**2 - quats[cond2, 2]**2
    sin_ph1 = 2 * quats[cond2, 1] * quats[cond2, 2]

    euler_angles[cond2, 0] = np.arctan2(sin_ph1, cos_ph1)
    euler_angles[cond2, 1] = np.pi

    # Otherwise
    cond3 = np.logical_not(np.logical_or(cond1, cond2))

    q01 = P * quats[cond3, 0] * quats[cond3, 1]
    q23 = quats[cond3, 2] * quats[cond3, 3]
    q02 = P * quats[cond3, 0] * quats[cond3, 2]
    q13 = quats[cond3, 1] * quats[cond3, 3]

    cos_ph1 = -(q23 + q01) / chi[cond3]
    sin_ph1 = (q13 - q02) / chi[cond3]

    cos_phi = q03[cond3] - q12[cond3]
    sin_phi = 2 * chi[cond3]

    cos_ph2 = (q23 - q01) / chi[cond3]
    sin_ph2 = (q13 + q02) / chi[cond3]

    euler_angles[cond3, 0] = np.arctan2(sin_ph1, cos_ph1)
    euler_angles[cond3, 1] = np.arctan2(sin_phi, cos_phi)
    euler_angles[cond3, 2] = np.arctan2(sin_ph2, cos_ph2)

    euler_angles[euler_angles[:, 0] < 0., 0] += 2 * np.pi
    euler_angles[euler_angles[:, 2] < 0., 2] += 2 * np.pi

    if degrees:
        euler_angles = np.rad2deg(euler_angles)

    return euler_angles


def format_tensor33(tensor, fmt='', sym=False):
    'Also formats non-masked array.'
    str_out = ""
    for i, row in enumerate(tensor):
        start = i if sym else 0
        for x in row[start:]:
            if isinstance(x, np.ma.core.MaskedConstant):
                x = 0
            str_out += f" {x:{fmt}}"
        str_out += "\n"

    return str_out


def vec6_to_tensor33sym(vec):
    """[summary]

    Parameters
    ----------
    vec : np.ndarray of shape (.., 6)
        Order 11, 22, 33, 23, 13, 12

    Returns
    -------
    np.ndarray of shape (.., 3, 3)

    """
    tens = np.zeros(vec.shape[:-1] + (3, 3), dtype=vec.dtype)

    tens[..., 0, 0] = vec[..., 0]
    tens[..., 1, 1] = vec[..., 1]
    tens[..., 2, 2] = vec[..., 2]
    tens[..., 1, 2] = vec[..., 3]
    tens[..., 0, 2] = vec[..., 4]
    tens[..., 0, 1] = vec[..., 5]

    tens[..., 2, 1] = tens[..., 1, 2]
    tens[..., 2, 0] = tens[..., 0, 2]
    tens[..., 1, 0] = tens[..., 0, 1]

    return tens
