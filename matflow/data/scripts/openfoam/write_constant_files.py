from pathlib import Path


FILES = {
    'g': r"""/*--------------------------------*- C++ -*----------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Version:  10
     \\/     M anipulation  |
\*---------------------------------------------------------------------------*/
FoamFile
{
    format      ascii;
    class       uniformDimensionedVectorField;
    location    "constant";
    object      g;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 1 -2 0 0 0 0];
value           (0 0 0);


// ************************************************************************* //
""",
    'LaserProperties': r"""/*--------------------------------*- C++ -*----------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Version:  6
     \\/     M anipulation  |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      PhaseFieldProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
V_incident	(0 1 0);//(0 1 0);//NORMALISED IN CODE

HS_a 0.0005;
HS_bg 0.0;//20
HS_velocity 0.0;//6.0;
HS_lg 1e-3;
HS_Q 2000;//2000.0;//

wavelength	1.064e-6;
e_num_density	5.83e29;
elec_resistivity	1.0e-6;

// Use local search: defaults to yes
//useLocalSearch yes;

// Print extra debug information: defaults to no
debug no;

Radius_Flavour	3.0;
""",
    'momentumTransport': r"""/*--------------------------------*- C++ -*----------------------------------*\
  =========                 |
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
    object      momentumTransport;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

simulationType  laminar;


// ************************************************************************* //
""",
    'phaseProperties': r"""/*--------------------------------*- C++ -*----------------------------------*\
  =========                 |
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
    object      phaseProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

phases          (metal gas);

sigma           0.07;

dsigmadT	-0.5e-4;

p0		100000.0;
Tvap 3068.0;
Mm 5.58e-2;
LatentHeatVap 7.45e6;
// ************************************************************************* //
""",
    'physicalProperties': r"""/*--------------------------------*- C++ -*----------------------------------*\
  =========                 |
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
    object      physicalProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //


Cv	500;

kappa	20.0;

rho_0	7800;

sigma_Y_0	250e6;

Hardening true;


K_0	100e6;
K_n	0.5;
K_B	1.0;
K_Beta_0	1e-3;
K_Beta_1	0.0;

// ************************************************************************* //
""",
}


def write_constant_files(path):
    output_dir = Path(path).parent
    for filename, contents in FILES.items():
        (output_dir / filename).write_bytes(contents.encode("utf-8"))
