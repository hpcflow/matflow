from pathlib import Path


TEMPLATE = r"""/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  3.0.1                                 |
|   \\  /    A nd           | Web:      www.OpenFOAM.org                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       volVectorField;
    location    "0";
    object      U;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 1 -1 0 0 0 0];

internalField   uniform (0 0 0);

boundaryField
{
	frontAndBack{
//            type            zeroGradient;
type            slip;

       // type            fixedValue;
       // value           uniform (0 0 0);
	}
    lowerWall
    {
    
    type uniformFixedValue;
    uniformValue table
    (
        (0 (0 0 0))
        (1.0e-8 (0 -5e2 0))
        (2.0e-8 (0 0 0))
        (3.0e-8 (0 0.0 0))
        (4.0e-8 (0 0 0))
    );

/*
        type            fixedValue;
        value           uniform (0 100 0);
*/
    }
    atmosphere
    {
//    type            noSlip;
    type            slip;

//        type            fixedValue;
//        value           uniform (0 -5 0);
    
  /*  
type pressureInletOutletVelocity;
phi phi;
rho rho;
tangentialVelocity uniform (0 0 0);
value uniform (0 0 0.0);
*/
    }
    defaultFaces
    {
        type            empty;
    }
}


// ************************************************************************* //
"""


def write_fifty_grains_initial_velocity(path):
    Path(path).write_text(TEMPLATE)
