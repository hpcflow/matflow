import numpy as np
import torch
from lightning.pytorch import seed_everything
import damask

from lvae3d.models.ResNetVAE_3Deu import ResNet18_3DVAEeu
from lvae3d.LightningVAETrainers import VAETrainerAlpha
from lvae3d.util.MetadataDicts import MetadataAlpha


def get_3dvae_fingerprint(volume_element, checkpoint_path, metadata_path, family):
    """Get fingerprint from PyTorch tensor of normalised Euler angles.

    Parameters
    ----------
    volume_element : dict
        Dream3D volume element (output from generate_volume_element schema).
    checkpoint_path : str
        Path to checkpoint. Should be a .ckpt file.
    metadata_path : str
        Path to metadata. Should be a .yaml file.

    Returns
    -------
    reconstruction: torch.Tensor
        Reconstructed RVE from the trained VAE.
    fingerprint: torch.Tensor
        Fingerprint from the trained VAE encoder.
    """
    seed_everything(42, workers=True)
    vae = ResNet18_3DVAEeu
    oris = convert_ori_rep(volume_element['orientations'])
    assert not oris['euler_degrees']
    euler_angles = oris['eulers']
    euler_angles = damask.Orientation(rotation=damask.Rotation.from_Euler_angles(euler_angles), family=family).reduced.as_Euler_angles()
    euler_angles /= np.pi * np.array([2, 1, 2])

    grain_image = volume_element['element_material_idx'][:]
    eulers_image = np.zeros(grain_image.shape + (3, ))
    for grain_i in range(len(euler_angles)):
        eulers_image[grain_image == grain_i] = euler_angles[grain_i]
    eulers_image = np.moveaxis(eulers_image, 3, 0)
    eulers_image = torch.from_numpy(eulers_image)

    eulers_image = torch.unsqueeze(eulers_image, 0)
    eulers_image = eulers_image.float()

    metadata = MetadataAlpha()
    metadata.load(metadata_path)
    model = VAETrainerAlpha.load_from_checkpoint(checkpoint_path, vae=vae,  metadata=metadata, weights_only=True)
    model.eval()
    _, mu, _ = model.vae.module.encoder(eulers_image)

    return {"fingerprint": mu.cpu().detach().numpy()}


def convert_ori_rep(ori_dict, type_out='euler'):
    if type_out != 'euler' and ori_dict.get('type') != 'quat':
        raise NotImplementedError('Can only convert euler to quat.')

    assert ori_dict.get('quat_component_ordering') == 'scalar-vector'

    return {
        'type': 'euler',
        'unit_cell_alignment': ori_dict.get('unit_cell_alignment'),
        'euler_degrees': False,
        'eulers': qu2eu(ori_dict['quaternions'], P=ori_dict.get('P', -1)),
    }# orientation_coordinate_system??


def qu2eu(qu: np.ndarray, P=1) -> np.ndarray:
    """
    Quaternion to Bunge Euler angles.

    References
    ----------
    E. Bernardes and S. Viollet, PLoS ONE 17(11):e0276302, 2022
    https://doi.org/10.1371/journal.pone.0276302

    Source
    ------
    https://github.com/eisenforschung/DAMASK/blob/release/python/damask/_rotation.py

    """
    a =    qu[...,0:1]
    b = -P*qu[...,3:4]
    c = -P*qu[...,1:2]
    d = -P*qu[...,2:3]

    eu = np.block([
        np.arctan2(b,a),
        np.arccos(2*(a**2+b**2)/(a**2+b**2+c**2+d**2)-1),
        np.arctan2(-d,c),
    ])

    eu_sum  = eu[...,0] + eu[...,2]
    eu_diff = eu[...,0] - eu[...,2]

    is_zero  = np.isclose(eu[...,1],0.0)
    is_pi    = np.isclose(eu[...,1],np.pi)
    is_ok    = ~np.logical_or(is_zero,is_pi)

    eu[...,0][is_zero] =  2*eu[...,0][is_zero]
    eu[...,0][is_pi]   = -2*eu[...,2][is_pi]
    eu[...,2][~is_ok]  = 0.0
    eu[...,0][is_ok]   = eu_diff[is_ok]
    eu[...,2][is_ok]   = eu_sum [is_ok]

    eu[np.logical_or(np.abs(eu)         < 1.e-6,
                        np.abs(eu-2*np.pi) < 1.e-6)] = 0.
    return np.where(eu < 0., eu%(np.pi*np.array([2.,1.,2.])), eu)
