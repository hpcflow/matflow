from pathlib import Path


def dump_mesh(path, gmsh_mesh_str):
    with Path("mesh.msh").open("wt", newline="\n") as fh:
        fh.write(gmsh_mesh_str)
