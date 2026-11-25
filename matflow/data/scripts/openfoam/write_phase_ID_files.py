from pathlib import Path
from textwrap import dedent

import numpy as np


TEMPLATE = dedent(
    """\
    /*--------------------------------*- C++ -*----------------------------------*\\
      =========                 |
      \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
       \\\\    /   O peration     | Website:  https://openfoam.org
        \\\\  /    A nd           | Version:  10
         \\\\/     M anipulation  |
    \\*---------------------------------------------------------------------------*/
    FoamFile
    {{
        format      ascii;
        class       volScalarField;
        location    "0.001";
        object      n.{grain_id};
    }}
    // * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

    dimensions      [0 0 0 0 0 0 0];

    internalField   nonuniform List<scalar>
    {num_voxels}
    (
    {grain_bool_str}
    );

    boundaryField
    {{
    {boundary_field}
    }}

    // ************************************************************************* //
    """
)


def write_phase_ID_files(path, volume_element, boundary_field):
    element_material_idx = np.asarray(volume_element["element_material_idx"][:])
    grid_size = np.asarray(volume_element["grid_size"][:], dtype=int)
    num_voxels = int(np.prod(grid_size))
    if element_material_idx.size != num_voxels:
        raise ValueError(
            "The number of element material indices does not match the volume-element grid."
        )

    material_ids = element_material_idx.flatten(order="F")
    num_constituents = len(volume_element["constituent_material_idx"])
    phase_ids = np.arange(num_constituents)
    if np.any(material_ids < 0) or np.any(material_ids >= num_constituents):
        raise ValueError(
            "Element material indices must refer to a declared volume-element constituent."
        )

    boundary_text = "\n".join(
        "    {patch_name}\n"
        "    {{\n"
        "        type            {type};\n"
        "    }}".format(**patch)
        for patch in boundary_field
    )
    output_dir = Path(path).parent
    for grain_id in phase_ids:
        grain_bool = (material_ids == grain_id).astype(int)
        file_text = TEMPLATE.format(
            grain_id=int(grain_id),
            num_voxels=num_voxels,
            grain_bool_str="\n".join(str(value) for value in grain_bool),
            boundary_field=boundary_text,
        )
        (output_dir / f"n.{int(grain_id)}").write_text(file_text)
