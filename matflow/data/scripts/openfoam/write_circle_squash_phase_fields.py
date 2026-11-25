from pathlib import Path
from textwrap import dedent

import numpy as np


PHASE_FIELD_SHAPE = (2, 57_600)

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
        location    "0.4";
        object      n.{phase_id};
    }}
    // * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

    dimensions      [0 0 0 0 0 0 0];

    internalField   nonuniform List<scalar> 
    {num_voxels}
    (
    {values}
    )
    ;

    boundaryField
    {{
    {boundary_field}
    }}


    // ************************************************************************* //
    """
)


def _format_boundary_field(boundary_field):
    patches = []
    for patch in boundary_field:
        patch_name = patch["patch_name"]
        patch_type = patch["type"]
        if patch_name in ("Front", "Back"):
            indent = "    \t" if patch_name == "Front" else "\t"
            patches.append(f"{indent}{patch_name}{{\ntype {patch_type};\n\t}}")
        else:
            patches.append(
                f"    {patch_name}\n"
                "    {\n"
                f"        type            {patch_type};\n"
                "    }"
            )
    return "\n".join(patches)


def write_circle_squash_phase_fields(path, phase_field_data, boundary_field):
    with np.load(Path(phase_field_data), allow_pickle=False) as archive:
        phase_fields = archive["phase_fields"]

    if phase_fields.shape != PHASE_FIELD_SHAPE:
        raise ValueError(
            "The Circle Squash phase-field data must have shape "
            f"{PHASE_FIELD_SHAPE}, got {phase_fields.shape}."
        )
    if not np.all(np.isfinite(phase_fields)):
        raise ValueError("The Circle Squash phase-field data must be finite.")

    output_dir = Path(path).parent
    boundary_text = _format_boundary_field(boundary_field)
    for phase_id, values in enumerate(phase_fields):
        file_text = TEMPLATE.format(
            phase_id=phase_id,
            num_voxels=values.size,
            values="\n".join(format(value, ".6g") for value in values),
            boundary_field=boundary_text,
        )
        (output_dir / f"n.{phase_id}").write_text(file_text)
