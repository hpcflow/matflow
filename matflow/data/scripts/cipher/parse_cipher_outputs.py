from cipher_parse import CIPHEROutput


def parse_cipher_outputs(
    cipher_VTU_files,
    num_VTU_files,
    VTU_files_time_interval,
    derive_outputs,
    save_outputs,
    delete_VTIs,
    delete_VTUs,
):

    out = CIPHEROutput.parse(
        directory=".",
        options={
            "num_VTU_files": num_VTU_files,
            "VTU_files_time_interval": VTU_files_time_interval,
            "derive_outputs": derive_outputs,
            "save_outputs": save_outputs,
            "delete_VTIs": delete_VTIs,
            "delete_VTUs": delete_VTUs,
        },
    )

    # # GBs in initial geom:
    # out.cipher_input.geometry.get_grain_boundaries()

    # # GBs in subsequent geoms:
    # out.set_all_geometries()
    # for geom in out.geometries:
    #     geom.get_grain_boundaries()

    phase_field_output = out.to_JSON(keep_arrays=True)
    return {"phase_field_output": phase_field_output}
