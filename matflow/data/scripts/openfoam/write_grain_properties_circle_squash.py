from textwrap import dedent
import numpy as np


DEFAULT_GRAIN_PROPERTIES = r"""/*--------------------------------*- C++ -*----------------------------------*\
                                                       |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Version:  10
     \\/     M anipulation  |
\*---------------------------------------------------------------------------*/
FoamFile
{
    format      ascii;
    class       dictionary;
    location    "constant";
    object      GrainProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

interface_width	4e-6;

N_Phases	2;

N_Materials	2;

Phase2Material (0 1);

phi1 (0.26 0);

phi2 (0 0);

phi3 (0 0);






n_constitutive_substeps	25;



//Interface Stuff


Energy
(
(Material.0 Material.0) 0.3
(Material.0 Material.1) 0.2
(Material.1 Material.1) 0.1
);

Mobility
(
(Material.0 Material.0) 5.1e-6
(Material.0 Material.1) 5.0e-4//100.0e-4//10 too high
(Material.1 Material.1) 5.3e-6
);



Material.0 //Fe 35Ni
{

Cv	500;

kappa	20.0;

rho_0	7500;

  C0000    1.40E10;	//	1.40E11; 	9.20E10;	1.11E11
  C1111    1.40E10;
  C2222    1.40E10;

  C1010    1.11E10;
  C2020    1.11E10;
  C0011    9.20E9;
  C1001    1.11E10;
  C0022    9.20E9;
  C2002    1.11E10;
  C0110    1.11E10;
  C1100    9.20E9;
  C0101    1.11E10;
  C2121    1.11E10;
  C1122    9.20E9;
  C2112    1.11E10;
  C0220    1.11E10;
  C2200    9.20E9;
  C1221    1.11E10;
  C2211    9.20E9;
  C0202    1.11E10;
  C1212    1.11E10;


N_slips	12;//

n0	(0	0.707106781186548	0.707106781186548); //slip normals
n1	(0	0.707106781186548	0.707106781186548);
n2	(0.707106781186548	0	0.707106781186548);
n3	(0.707106781186548	0	0.707106781186548);
n4	(0.707106781186548	0.707106781186548	0);
n5	(0.707106781186548	0.707106781186548	0);
n6	(0	-0.707106781186548	0.707106781186548);
n7	(0	-0.707106781186548	0.707106781186548);
n8	(0.707106781186548	0	-0.707106781186548);
n9	(0.707106781186548	0	-0.707106781186548);
n10	(-0.707106781186548	0.707106781186548	0);
n11	(-0.707106781186548	0.707106781186548	0);

m0 (0.577350269189626	-0.577350269189626	0.577350269189626); //slip directions
m1 (0.577350269189626	0.577350269189626	-0.577350269189626);
m2 (-0.577350269189626	0.577350269189626	0.577350269189626);
m3 (0.577350269189626	0.577350269189626	-0.577350269189626);
m4 (-0.577350269189626	0.577350269189626	0.577350269189626);
m5 (0.577350269189626	-0.577350269189626	0.577350269189626);
m6 (0.577350269189626	0.577350269189626	0.577350269189626);
m7 (-0.577350269189626	0.577350269189626	0.577350269189626);
m8 (0.577350269189626	0.577350269189626	0.577350269189626);
m9 (0.577350269189626	-0.577350269189626	0.577350269189626);
m10 (0.577350269189626	0.577350269189626	0.577350269189626);
m11 (0.577350269189626	0.577350269189626	-0.577350269189626);




initialCRSS	16e5;
tau_S	300e6;
h_0	1000e6;
r	1.4;
k_exponent	20.0;
gammadot_0	1e-3;

}

Material.1	// 
{

Cv	500;

kappa	20.0;

rho_0	7800;

  C0000    1.40E11;	//	1.40E11; 	9.20E10;	1.11E11
  C1111    1.40E11;
  C2222    1.40E11;

  C1010    1.11E11;
  C2020    1.11E11;
  C0011    9.20E10;
  C1001    1.11E11;
  C0022    9.20E10;
  C2002    1.11E11;
  C0110    1.11E11;
  C1100    9.20E10;
  C0101    1.11E11;
  C2121    1.11E11;
  C1122    9.20E10;
  C2112    1.11E11;
  C0220    1.11E11;
  C2200    9.20E10;
  C1221    1.11E11;
  C2211    9.20E10;
  C0202    1.11E11;
  C1212    1.11E11;


N_slips	12;//

n0	(0	0.707106781186548	0.707106781186548); //slip normals
n1	(0	0.707106781186548	0.707106781186548);
n2	(0.707106781186548	0	0.707106781186548);
n3	(0.707106781186548	0	0.707106781186548);
n4	(0.707106781186548	0.707106781186548	0);
n5	(0.707106781186548	0.707106781186548	0);
n6	(0	-0.707106781186548	0.707106781186548);
n7	(0	-0.707106781186548	0.707106781186548);
n8	(0.707106781186548	0	-0.707106781186548);
n9	(0.707106781186548	0	-0.707106781186548);
n10	(-0.707106781186548	0.707106781186548	0);
n11	(-0.707106781186548	0.707106781186548	0);

m0 (0.577350269189626	-0.577350269189626	0.577350269189626); //slip directions
m1 (0.577350269189626	0.577350269189626	-0.577350269189626);
m2 (-0.577350269189626	0.577350269189626	0.577350269189626);
m3 (0.577350269189626	0.577350269189626	-0.577350269189626);
m4 (-0.577350269189626	0.577350269189626	0.577350269189626);
m5 (0.577350269189626	-0.577350269189626	0.577350269189626);
m6 (0.577350269189626	0.577350269189626	0.577350269189626);
m7 (-0.577350269189626	0.577350269189626	0.577350269189626);
m8 (0.577350269189626	0.577350269189626	0.577350269189626);
m9 (0.577350269189626	-0.577350269189626	0.577350269189626);
m10 (0.577350269189626	0.577350269189626	0.577350269189626);
m11 (0.577350269189626	0.577350269189626	-0.577350269189626);



initialCRSS	160e6;
tau_S	300e6;
h_0	1000e6;
r	1.4;
k_exponent	20.0;
gammadot_0	1e-3;

}

// ************************************************************************* //
"""


def write_grain_properties_circle_squash(path, volume_element, orientations, materials):
    if not materials:
        path.write_text(DEFAULT_GRAIN_PROPERTIES)
        return

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

        interface_width	{interface_width};

        n_constitutive_substeps	{n_constitutive_substeps};

        N_Phases	{num_grains};

        N_Materials	{num_materials};

        Phase2Material ({phase_mat_idx}); // material index for each grain

        phi1 ({phi1});
        phi2 ({phi2});
        phi3 ({phi3});

        // Interface stuff

        Energy
        (
        {interface_energy}
        );

        Mobility
        (
        {interface_mobility}
        );

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

    grain_phase_labels = volume_element["constituent_phase_label"][:]
    uniq_phase_labs, grain_phase_idx = np.unique(grain_phase_labels, return_inverse=True)
    if len(materials) != len(uniq_phase_labs):
        raise ValueError(
            "The number of supplied materials must equal the number of unique "
            "phase labels in volume_element."
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

    num_materials = len(uniq_phase_labs)
    interface_energy = "\n".join(
        f"(Material.{i} Material.{j}) "
        f"{materials[0].get('interface_energy', 0.3 if i != 1 or j != 1 else 0.1)}"
        for i in range(num_materials)
        for j in range(i, num_materials)
    )
    interface_mobility = "\n".join(
        f"(Material.{i} Material.{j}) "
        f"{materials[0].get('interface_mobility', 5.0e-4 if i != j else (5.1e-6 if i == 0 else 5.3e-6))}"
        for i in range(num_materials)
        for j in range(i, num_materials)
    )

    num_grains = len(np.unique(volume_element["element_material_idx"]))

    if orientations.representation.type.name != "EULER":
        raise ValueError("GrainProperties generation requires Euler orientations.")
    if orientations.representation.euler_is_degrees:
        raise ValueError("GrainProperties generation requires orientations in radians.")
    phi1, phi2, phi3 = orientations.data.T

    file_str = TEMPLATE.format(
        interface_width=materials[0].get("interface_width", 4e-6),
        n_constitutive_substeps=materials[0].get("n_constitutive_substeps", 25),
        num_grains=num_grains,
        num_materials=len(uniq_phase_labs),
        phase_mat_idx=" ".join(str(i) for i in grain_phase_idx),
        phi1=" ".join(str(i) for i in phi1),
        phi2=" ".join(str(i) for i in phi2),
        phi3=" ".join(str(i) for i in phi3),
        interface_energy=interface_energy,
        interface_mobility=interface_mobility,
        materials="\n\n".join(mat_strs),
    )
    path.write_text(file_str)
