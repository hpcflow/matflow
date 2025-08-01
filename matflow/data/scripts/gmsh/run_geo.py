import gmsh


def run_geo(gmsh_geo_file):

    # Initialize Gmsh
    gmsh.initialize()

    # Run the .geo file
    gmsh.open(gmsh_geo_file)
    gmsh.write("mesh.msh")

    # Finalize Gmsh
    gmsh.finalize()
