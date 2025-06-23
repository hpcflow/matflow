import numpy as np


def write_mesh(path, volume_element):
    np.savez(
        path,
        num_cells=volume_element["grid_size"][:],  # i.e. Nx, Ny, Nz
        domain=np.asarray(volume_element["size"]),  # i.e. domain_x, domain_y, domain_z
        cell_grain_indices=volume_element["element_material_idx"][:].reshape(
            -1
        ),  # TODO: check order!
        quaternions=volume_element["orientations"]["quaternions"][:],
        grain_orientation_indices=volume_element["constituent_orientation_idx"][:],
    )
