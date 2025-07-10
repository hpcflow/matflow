from cipher_parse import CIPHERInput


def write_cipher_input(path, phase_field_input, separate_mapping_files):
    inp = CIPHERInput.from_JSON(phase_field_input)
    inp.write_yaml(path, separate_mappings=separate_mapping_files)
    inp.geometry.write_VTK("initial.vti")
