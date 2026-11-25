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

interface_width	1e-6;

N_Phases	50;

N_Materials	1;

Phase2Material (0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0);

phi1 (1.1185292252521302 1.4447354316095231 0.4418076427205522 0.8530964632480889 0.2256736041635418 0.8778181990690479 0.28893389967680844 1.4821403271232094 0.5279850483249845 0.7335488091591938 0.0050517704947168 0.7461245501097481 0.04331522899551642 0.18376453475936186 0.8737657483512539 1.0479610117133324 1.0370853794674204 1.3358536472158642 0.7270111513321988 1.1231279090155373 1.0219072154061983 1.1222867227074387 1.0740825046036535 1.0892504093829918 0.30615683308443 1.4406599689995656 0.9616928149698312 0.5728359656881788 0.0647502644835528 0.5399595809172536 1.5260439316068108 0.7969174480605485 0.3729319572336154 0.5971306105890536 0.8360319050729306 0.02204376760591027 1.175840205032166 0.05490700330997343 1.1415810980454761 1.1808700329913915 0.6446360318191175 0.59826544449569 0.2274238357518184 1.5358223895095562 1.4950043439518532 1.0074698904851485 0.5301300995294745 1.290945076295934 0.8379107884407556 0.5933049462526289);
phi2 (0.10 0.33 1.09 0.93 0.54 0.01 1.31 0.11 0.90 1.30 0.12 0.45 1.01 0.09 0.90 0.34 0.14 0.66 0.26 0.08 0.89 1.01 0.02 1.25 0.11 0.31 1.40 0.82 1.37 1.05 0.36 0.31 0.58 0.86 0.62 1.30 1.12 1.01 1.47 0.62 0.03 0.48 0.68 0.67 0.84 0.07 0.74 0.42 1.38 0.55);
phi3 (0.7196744993498547 1.0159068604606336 1.3400816082718228 1.3497604488394435 0.4475760676439134 0.26956518537493457 0.6122362914034659 0.0753408312737558 0.6467560339893723 1.0629196929448224 1.2971860904579235 1.0708571671962304 1.0733381951959429 1.1229574317054736 0.1749214150770773 1.3433927622323587 1.3899757545347284 1.0787951531372146 0.742080590693915 0.44715655909244023 0.7562760665162016 1.44388851504748 1.3055040087248828 1.4545113818193036 0.182468803822151 0.9561846830632148 0.6138604717963478 0.36226558723576546 0.43783967346252867 1.1749186158439402 0.18981152783360533 0.3105947446898946 1.5602382650396498 1.4030066523240927 1.357811599295094 1.1827707198649966 0.8214048324023381 1.4349737738103219 1.2503276139473463 0.15482869220677603 1.2882320739535171 0.029566788515600486 0.7521558971909416 0.7308933995596678 1.5177314082617945 0.6874398265842135 0.15512550662091523 0.8338295208628755 0.9670165584910202 0.203134226610729);



n_constitutive_substeps	10;






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


//Material Stuff


Material.0 //Fe 35Ni
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



initialCRSS	16e6;
tau_S	148e6;
h_0	180e6;
r	1.1;
k_exponent	5.0;
gammadot_0	1e-3;

}

Material.1	// W
{

Cv	500;

kappa	20.0;

rho_0	7800;

  
  C0000    50.1e10;
  C1111    50.1e10;
  C2222    50.1e10;

  C1010    15.1e10;
  C2020    15.1e10;
  C0011    19.8e10;
  C1001    15.1e10;
  C0022    19.8e10;
  C2002    15.1e10;
  C0110    15.1e10;
  C1100    19.8e10;
  C0101    15.1e10;
  C2121    15.1e10;
  C1122    19.8e10;
  C2112    15.1e10;
  C0220    15.1e10;
  C2200    19.8e10;
  C1221    15.1e10;
  C2211    19.8e10;
  C0202    15.1e10;
  C1212    15.1e10;
  
  N_slips	12;

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



initialCRSS	16e6;
tau_S	148e6;
h_0	180e6;
r	1.1;
k_exponent	10.0;

}

// ************************************************************************* //
"""


def write_grain_properties(path, volume_element, orientations, materials):
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

    num_grains = len(volume_element["constituent_material_idx"])

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
