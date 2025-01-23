from damask_parse import read_material, read_geom
from damask_parse.utils import validate_orientations, validate_volume_element


def generate_volume_element_from_damask_input_files(
    geom_path, material_path, orientations
):
    geom_dat = read_geom(geom_path)
    material_data = read_material(material_path)
    volume_element = {
        "element_material_idx": geom_dat["element_material_idx"],
        "grid_size": geom_dat["grid_size"],
        "size": geom_dat["size"],
        **material_data["volume_element"],
    }

    if orientations is not None:
        orientations = validate_orientations(orientations)
        num_supplied_ori = orientations["quaternions"].shape[0]
        num_material_ori = volume_element["orientations"]["quaternions"].shape[0]
        if num_supplied_ori != num_material_ori:
            raise ValueError(
                f"Number of orientations supplied {num_supplied_ori} is different to "
                f"number in the material file {num_material_ori}."
            )

        volume_element["orientations"] = orientations

    volume_element = validate_volume_element(volume_element)
    out = {"volume_element": volume_element}
    return out
