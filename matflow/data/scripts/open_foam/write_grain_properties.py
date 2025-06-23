from textwrap import dedent

import numpy as np


def write_grain_properties(path, volume_element, orientations, materials):
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
            class       dictionary;
            location    "constant";
            object      GrainProperties;
        }}
        // * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //


        N_Phases	{num_grains};

        N_Materials	{num_materials};

        Phase2Material ({phase_mat_idx}); // material index for each grain

        phi1 ({phi1});
        phi2 ({phi2});
        phi3 ({phi3});


        {materials}
    """
    )

    MAT_TEMPLATE = dedent(
        R"""
        Material.{mat_idx} // {mat_label}
        {{
        
        {elasticity_tensor}

        N_slips {num_slips};

        {slip_planes}

        {slip_dirs}
        
        {mat_props}

        }}

        // ************************************************************************* //
        """
    )

    mat_strs = []
    for mat_idx, mat_i in enumerate(materials):
        slip_sys = mat_i["slip_systems"]

        mat_i_str = MAT_TEMPLATE.format(
            mat_idx=mat_idx,
            mat_label=mat_i["label"],
            elasticity_tensor="\n".join(
                f"{k}    {v:.2E};" for k, v in mat_i["elasticity"].items()
            ),
            num_slips=len(slip_sys),
            slip_planes="\n".join(
                f"m{s_idx:<3}({s_plane[0]:10.3f}{s_plane[1]:10.3f}{s_plane[2]:10.3f});"
                for s_idx, (s_plane, _) in enumerate(slip_sys)
            ),
            slip_dirs="\n".join(
                f"n{s_idx:<3}({s_dir[0]:10.3f}{s_dir[1]:10.3f}{s_dir[2]:10.3f});"
                for s_idx, (_, s_dir) in enumerate(slip_sys)
            ),
            mat_props="\n".join(f"{k:<20} {v};" for k, v in mat_i["properties"].items()),
        )
        mat_strs.append(mat_i_str)

    num_grains = len(np.unique(volume_element["element_material_idx"]))
    grain_phase_labels = volume_element["constituent_phase_label"][:]
    uniq_phase_labs, grain_phase_idx = np.unique(grain_phase_labels, return_inverse=True)

    assert orientations.representation.type.name == "EULER"
    assert not orientations.representation.euler_is_degrees
    phi1, phi2, phi3 = orientations.data.T

    file_str = TEMPLATE.format(
        num_grains=num_grains,
        num_materials=len(uniq_phase_labs),
        phase_mat_idx=" ".join(str(i) for i in grain_phase_idx),
        phi1=" ".join(str(i) for i in phi1),
        phi2=" ".join(str(i) for i in phi2),
        phi3=" ".join(str(i) for i in phi3),
        materials="\n\n".join(mat_strs),
    )
    with path.open("wt") as fp:
        fp.write(file_str)
