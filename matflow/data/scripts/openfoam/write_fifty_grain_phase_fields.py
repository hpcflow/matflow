from pathlib import Path
from textwrap import dedent

import numpy as np

from matflow.data.scripts.openfoam.load_fifty_grain_phase_fields import (
    load_fifty_grain_phase_fields,
)


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

    internalField   {internal_field}

    boundaryField
    {{
    {boundary_field}
    }}


    // ************************************************************************* //
    """
)


def write_fifty_grain_phase_fields(path, phase_field_data, boundary_field):
    phase_fields = load_fifty_grain_phase_fields(phase_field_data)
    boundary_text = "\n".join(
        "    {patch_name}\n"
        "    {{\n"
        "        type            {type};\n"
        "    }}".format(**patch)
        for patch in boundary_field
    )

    output_dir = Path(path).parent
    num_voxels = phase_fields.shape[1]
    for grain_id, values in enumerate(phase_fields):
        if np.all(values == 0):
            internal_field = "uniform 0;"
        else:
            values_text = "\n".join(format(value, ".6g") for value in values)
            internal_field = (
                "nonuniform List<scalar> \n"
                f"{num_voxels}\n"
                "(\n"
                f"{values_text}\n"
                ")\n;"
            )
        file_text = TEMPLATE.format(
            grain_id=grain_id,
            internal_field=internal_field,
            boundary_field=boundary_text,
        )
        (output_dir / f"n.{grain_id}").write_text(file_text)
