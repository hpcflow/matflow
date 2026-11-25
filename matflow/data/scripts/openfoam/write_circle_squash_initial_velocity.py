from pathlib import Path
from string import Template


TEMPLATE = Template(
    r"""/*--------------------------------*- C++ -*----------------------------------*\
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

    Front
    {
type codedFixedValue;
value $$internalField;
name velocityProfilefront;

code
#{
vectorField veloc(patch().size(), vector(0, 0, 0));
scalar radius=$velocity_radius;
scalar Peak=$negative_peak;
scalar P =4.0;

            const vectorField& centre(patch().Cf());
            forAll(centre, i)
            {
                veloc[i].z() =((Peak))*Foam::exp(-Foam::pow(1.0*Foam::pow((centre[i].y()-0.1e-3),2.0)/(2.0*radius*radius),P));
            if(centre[i].y()<0.005e-3||centre[i].y()>0.195e-3)
            {
            veloc[i].z() =0.0;
            }
            }
            

operator==(veloc);
#};
    }
    Back
    {
type codedFixedValue;
value $$internalField;
name velocityProfileback;

code
#{
vectorField veloc(patch().size(), vector(0, 0, 0));
scalar radius=$velocity_radius;
scalar Peak=$positive_peak;
scalar P =4.0;

            const vectorField& centre(patch().Cf());
            forAll(centre, i)
            {
                veloc[i].z() =((Peak))*Foam::exp(-Foam::pow(1.0*Foam::pow((centre[i].y()-0.1e-3),2.0)/(2.0*radius*radius),P));
                if(centre[i].y()<0.005e-3||centre[i].y()>0.195e-3)
            {
            veloc[i].z() =0.0;
            }
            }
            

operator==(veloc);
#};
    }
    
    lowerWall
    {
type codedFixedValue;
value $$internalField;
name velocityProfilebottom;

code
#{
vectorField veloc(patch().size(), vector(0, 0, 0));
scalar radius=$velocity_radius;
scalar Peak=$negative_peak;
scalar P =4.0;

            const vectorField& centre(patch().Cf());
            forAll(centre, i)
            {
                veloc[i].y() =((Peak))*Foam::exp(-Foam::pow(1.0*Foam::pow((centre[i].z()-0.1e-3),2.0)/(2.0*radius*radius),P));
            if(centre[i].z()<0.005e-3||centre[i].z()>0.195e-3)
            {
            veloc[i].y() =0.0;
            }
            }
            

operator==(veloc);
#};
    }
    atmosphere
    {
type codedFixedValue;
value $$internalField;
name velocityProfiletop;

code
#{
vectorField veloc(patch().size(), vector(0, 0, 0));
scalar radius=$velocity_radius;
scalar Peak=$positive_peak;
scalar P =4.0;

            const vectorField& centre(patch().Cf());
            forAll(centre, i)
            {
                veloc[i].y() =((Peak))*Foam::exp(-Foam::pow(1.0*Foam::pow((centre[i].z()-0.1e-3),2.0)/(2.0*radius*radius),P));
            if(centre[i].z()<0.005e-3||centre[i].z()>0.195e-3)
            {
            veloc[i].y() =0.0;
            }
            }
            

operator==(veloc);
#};
    }
    defaultFaces
    {
        type            empty;
    }
}


// ************************************************************************* //
"""
)


def write_circle_squash_initial_velocity(path, peak_velocity, velocity_radius):
    if peak_velocity is None or velocity_radius is None:
        raise ValueError("peak_velocity and velocity_radius are required.")

    if peak_velocity < 0:
        raise ValueError("peak_velocity must be non-negative.")
    if velocity_radius <= 0:
        raise ValueError("velocity_radius must be positive.")

    peak_text = "50.0" if peak_velocity == 50.0 else f"{peak_velocity:.12g}"
    radius_text = "0.05e-3" if velocity_radius == 0.05e-3 else f"{velocity_radius:.12g}"
    text = TEMPLATE.substitute(
        velocity_radius=radius_text,
        negative_peak="-" + peak_text,
        positive_peak=peak_text,
    )
    Path(path).write_text(text)
