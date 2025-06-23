from textwrap import dedent

import numpy as np


def write_phase_ID_files(path, volume_element):
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
            location    "0.1";
            object      n.{grain_id};
        }}
        // * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

        dimensions      [0 0 0 0 0 0 0];

        internalField   nonuniform List<scalar> 
        {num_voxels}
        (
        {grain_bool_str}      
        )
        ;

        boundaryField
        {{
            lowerWall
            {{
                type            zeroGradient;
            }}
            atmosphere
            {{
                type            zeroGradient;
            }}
            rightWall
            {{
                type            empty;
            }}
            leftWall
            {{
                type            empty;
            }}
            frontAndBack
            {{
                type            zeroGradient;
            }}
        }}


        // ************************************************************************* //
    """
    )
    root_dir = path.parent
    print(f"{root_dir=!r}")

    # TODO: check flatten order (row-major, col-major)!
    micro_flat = volume_element["element_material_idx"][:].flatten()

    uniq_IDs = np.unique(micro_flat)
    print(uniq_IDs)

    num_voxels = np.prod(volume_element["grid_size"]).item()

    for grain_id in uniq_IDs:
        id_i_arr = (micro_flat == grain_id).astype(int)
        grain_bool_str = "\n".join(str(i) for i in id_i_arr)

        grain_n = TEMPLATE.format(
            num_voxels=num_voxels,
            grain_id=grain_id,
            grain_bool_str=grain_bool_str,
        )
        with root_dir.joinpath(f"n.{grain_id}").open("wt") as fp:
            fp.write(grain_n)
