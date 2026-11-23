from pathlib import Path


FILES = {
    "controlDict": r"""/*--------------------------------*- C++ -*----------------------------------*\
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
    class       dictionary;
    location    "system";
    object      controlDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
libs
(
    "libROUNDSchemes.so" 
);

application     Flint_multiphaseEulerFoamD;

startFrom       latestTime;

startTime       0;

stopAt          endTime;

endTime         5e-6;

deltaT          1e-10;

writeControl    adjustableRunTime;

writeInterval   1.0e-8;

purgeWrite      0;

writeFormat     ascii;

writePrecision  10;

writeCompression off;

timeFormat      general;

timePrecision   10;

runTimeModifiable yes;

adjustTimeStep  yes;

maxCo           0.1;//0.1;
maxAlphaCo      0.1;

maxDeltaT       5.0e-11;


// ************************************************************************* //
""",
    "decomposeParDict": r"""/*--------------------------------*- C++ -*----------------------------------*\
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
    location    "system";
    object      decomposeParDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

numberOfSubdomains 12;

method          scotch;

simpleCoeffs
{
    n               (1 2 2);
}

hierarchicalCoeffs
{
    n               (1 1 1);
    order           xyz;
}

manualCoeffs
{
    dataFile        "";
}

distributed     no;

roots           ( );


// ************************************************************************* //
""",
    "fvSchemes": r"""/*--------------------------------*- C++ -*----------------------------------*\
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
    location    "system";
    object      fvSchemes;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

 
ddtSchemes
{
    default         Euler;//backward;//Euler;
}

gradSchemes
{
    default         Gauss linear;//leastSquares;//Gauss linear;//
}

divSchemes
{
    div(rhoPhi,U)  Gauss linearUpwind grad(U);
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
    div(rhoPhi,epsilon1)	Gauss linear;//Gauss vanLeer01;
    div((interpolate(cp)*rhoPhi),T)   Gauss upwind;
    
    div(U)	Gauss linear;//cubic;
    
    div(sigma)	Gauss linear;
    
    div(phi,sigma)	Gauss linear;//linear;

    
    
    //div(testSIG)	Gauss linear;//cubic;
    
    div(interpolate(U),rho)	Gauss linear;
    
    div(rhoPhi,K)	Gauss upwind;//Gauss linear;
    div((Cv*rhoPhi),T)	Gauss upwind;//Gauss linear;
    div((sigma&U))	Gauss linear;
    div(phi,rho)	Gauss ROUNDAplus;//Gauss linear;//Gauss ROUNDAplus;//Gauss linear;//Gauss ROUNDAplus;//
    
    
    div(rhoPhi,Acc_Strain)	Gauss ROUNDAplus;//Gauss linear;//Gauss ROUNDAplus;//Gauss linear;
    
    div(phi,Acc_Strain)	Gauss ROUNDAplus;//Gauss linear;//Gauss ROUNDAplus;//Gauss linear;
    
   
    "div\(rhoPhi,n.*\)"	Gauss ROUNDAplus01;//Gauss ROUNDAplus01;//;//Gauss linear;
    

    "div\(phi,g_alpha.*\)"	Gauss ROUNDAplus;//Gauss linear;
    
    "div\(rhoPhi,g_alpha.*\)"	Gauss ROUNDAplus;//Gauss linear;
    
   "div\(rhoPhi,gamma_alphas.*.*\)"	Gauss ROUNDAplus;//Gauss ROUNDAplus;//Gauss linear;
    
    div(rhoPhi,ROT.1)	Gauss ROUNDAplus;//Gauss linear;
    div(rhoPhi,ROT.2)	Gauss ROUNDAplus;//Gauss linear;
    div(rhoPhi,ROT.3)	Gauss ROUNDAplus;//Gauss linear;
    

	"div\(rhoPhi,ROT.*.*\)"	Gauss ROUNDAplus;//Gauss ROUNDAplus;//Gauss linear;
	
	
	"div\(rhoPhi,sigma.*\)"	Gauss ROUNDAplus;//
    
}

laplacianSchemes
{
    default         Gauss linear corrected;
}

interpolationSchemes
{
    default         linear;//linear;//linear;//
    //sigma	cubic;
}

snGradSchemes
{
    default         corrected;
}


// ************************************************************************* //
""",
    "fvSolution": r"""/*--------------------------------*- C++ -*----------------------------------*\
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
    location    "system";
    object      fvSolution;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

solvers
{


    U
    {
    /*
        solver          PBiCGStab;
        preconditioner  DILU;
        tolerance       1e-12;
        minIter         1;
        maxIter         5000;//2
      */ 
        
    /*
        solver           GAMG;
        tolerance        1e-012;
        relTol           0.0;
        smoother         DILUGaussSeidel;
     */   
        
        solver          smoothSolver;
        smoother        GaussSeidel;
        nSweeps         5;
        tolerance       1e-09;
        relTol          0.0;
        

        
    }
        UFinal
    {
        $U;
    }
    

    
    
        T
    {
/*
        solver          PBiCG;
        preconditioner  DILU;
        tolerance       1e-12;
        minIter         1;
        maxIter         500;//2
*/
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-6;
        relTol          0.0;
    }

    TFinal
    {
        $T;
    }
    
            rho
    {
/*
        solver          PBiCG;
        preconditioner  DILU;
        tolerance       1e-12;
        minIter         1;
        maxIter         500;//2
*/
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-9;
        relTol          0.0;
    }

    rhoFinal
    {
        $rho;
    }
    
    
                Acc_Strain
    {
/*
        solver          PBiCG;
        preconditioner  DILU;
        tolerance       1e-12;
        minIter         1;
        maxIter         500;//2
*/
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-6;
        relTol          0.0;
    }

    Acc_StrainFinal
    {
        $Acc_Strain;
    }
    

    
    
    
    
        sigma
    {
    /*
        solver          PCG;
        preconditioner  DIC;
        tolerance       1e-12;
        relTol          0.0;
        */
        
        solver           GAMG;
        tolerance        1e-012;
        relTol           0.0;
        smoother         DILUGaussSeidel;
    }

    sigmaFinal
    {
        $sigma;
        relTol          0;
    }
    
            "sigma.*"
    {

        solver           GAMG;
        tolerance        1e-09;
        relTol           0.0;
        smoother         DILUGaussSeidel;

    }

    "(sigma.*)Final"
    {
        solver           GAMG;
        tolerance        1e-012;
        relTol           0.0;
        smoother         DILUGaussSeidel;
    }
    
    
    
    
        "n.*"
    {

        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-6;
        relTol          0.0;

    }

    "(n.*)Final"
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-6;
        relTol          0.0;
    }
    
            "g_alpha.*"
    {

        solver          PBiCGStab;
        preconditioner  DILU;
        tolerance       1e-12;
        minIter         1;
        maxIter         5000;//2

    }

    "(g_alpha.*)Final"
    {
        solver          PBiCGStab;
        preconditioner  DILU;
        tolerance       1e-12;
        minIter         1;
        maxIter         5000;//2
    }
    
    
    
                "ROT.*"
    {

        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-6;
        relTol          0.0;

    }
    
        "(ROT.*)Final"
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-6;
        relTol          0.0;
    }
    
                    "gamma_alphas.*"
    {

        solver          PBiCGStab;
        preconditioner  DILU;
        tolerance       1e-8;
        relTol          0.01;
        maxIter         1000;

    }
    
        "(gamma_alphas.*)Final"
    {
        solver          PBiCGStab;
        preconditioner  DILU;
        tolerance       1e-8;
        relTol          0.01;
        maxIter         1000;
    }

    
}


PIMPLE
{
    momentumPredictor   no;
    nOuterCorrectors    5;//10
    nCorrectors         1;
    nNonOrthogonalCorrectors 0;
    
    relaxU              0.5;  //Relaxation for momentum-stress coupling between pimple iterations
    
    
}

relaxationFactors
{
    equations
    {
     //   ".*" 0.9;
     //   U	0.3;
    }
}


// ************************************************************************* //
""",
    "setFieldsDict": r"""/*--------------------------------*- C++ -*----------------------------------*\
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
    class       dictionary;
    location    "system";
    object      setFieldsDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

defaultFieldValues
(
   
);

regions
(



    /*boxToCell
    {
        box (-0.085 0.001 -0.05) (0.085 0.004 0.05);
        fieldValues
        (
    volScalarFieldValue alpha.metal 1
        );
    }
*/
/*
cylinderToCell
{
p1 	 (-1 	 0.0005 	 0.0);
p2 	 (51 	 0.0005 	 0.0);
radius 5e-4;
fieldValues
(
            volScalarFieldValue alpha.phase1 1
);
}

cylinderToCell
{
p1 	 (-1 	 0.0005 	 -1e-3);
p2 	 (51 	 0.0005 	 -1e-3);
radius 5e-4;
fieldValues
(
            volScalarFieldValue alpha.phase1 1
);
}
cylinderToCell
{
p1 	 (-1 	 0.0005 	 1e-3);
p2 	 (51 	 0.0005 	 1e-3);
radius 5e-4;
fieldValues
(
            volScalarFieldValue alpha.phase1 1
);
}

cylinderToCell
{
p1 	 (-1 	 0.000 	 2.5e-3);
p2 	 (51 	 0.000 	 2.5e-3);
radius 10e-4;
fieldValues
(
            volScalarFieldValue alpha.phase1 1
);
}

cylinderToCell
{
p1 	 (-1 	 0.0005 	 4e-3);
p2 	 (51 	 0.0005 	 4e-3);
radius 5e-4;
fieldValues
(
            volScalarFieldValue alpha.phase1 1
);
}

cylinderToCell
{
p1 	 (-1 	 0.0005 	 6e-3);
p2 	 (51 	 0.0005 	 6e-3);
radius 5e-4;
fieldValues
(
            volScalarFieldValue alpha.phase1 1
);
}
*/

);


// ************************************************************************* //
""",
}


def write_circle_squash_system_files(path):
    output_dir = Path(path).parent
    for filename, contents in FILES.items():
        (output_dir / filename).write_bytes(contents.encode("utf-8"))
