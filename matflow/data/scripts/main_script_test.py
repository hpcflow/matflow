import json
import matflow as mf
import h5py


def main_script_test(inputs_JSON_path, outputs_HDF5_path):
    with inputs_JSON_path.open("rt") as fp:
        inputs = json.load(fp)
    oris = mf.Orientations.from_random(number=inputs["num_orientations"])

    with h5py.File(outputs_HDF5_path, mode="w") as f:
        ori_grp = f.create_group("orientations")
        ori_grp.create_dataset(name="data", data=oris.data)
        ori_grp.attrs.create(
            name="representation",
            data=oris.representation.value,
        )
        ori_grp.attrs.create(
            name="unit_cell_alignment",
            data=[
                oris.unit_cell_alignment.x.value,
                oris.unit_cell_alignment.y.value,
                oris.unit_cell_alignment.z.value,
            ],
        )
