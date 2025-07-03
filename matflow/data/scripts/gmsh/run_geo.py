import gmsh


def run_geo(path):

    print(
        f"{path=!r}"
    )  # gmsh_mesh_file (i.e. the input file that should be generated here)

    geo_name = "script.geo"

    # Initialize Gmsh
    gmsh.initialize()

    # Run the .geo file (this includes a command to save the mesh file)
    gmsh.open(geo_name)

    # Finalize Gmsh
    gmsh.finalize()
