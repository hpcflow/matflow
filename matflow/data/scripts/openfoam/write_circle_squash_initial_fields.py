from pathlib import Path


FILES = {
    'T': r"""/*--------------------------------*- C++ -*----------------------------------*\
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
    class       volScalarField;
    object      p_rgh;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 0 0 1 0 0 0];

internalField   uniform 300.0;

boundaryField
{
	Front{
type zeroGradient;
	}
	Back{
type zeroGradient;
	}

    lowerWall
    {
type zeroGradient;
    }

    atmosphere
    {
type zeroGradient;
    }

    defaultFaces
    {
        type            empty;
    }
}

// ************************************************************************* //
""",
}


def write_circle_squash_initial_fields(path):
    output_dir = Path(path).parent
    for filename, contents in FILES.items():
        (output_dir / filename).write_bytes(contents.encode("utf-8"))
