from pathlib import Path
import gmsh


def run_geo(gmsh_geo_file):

    # Initialize Gmsh
    gmsh.initialize()

    # Run the .geo file
    gmsh.open(gmsh_geo_file)
    gmsh.write("mesh.msh")

    # Finalize Gmsh
    gmsh.finalize()

    file = Path("mesh.msh")
    with file.open("rt") as fh:
        string = fh.read()

    return {"gmsh_mesh_str": string}
