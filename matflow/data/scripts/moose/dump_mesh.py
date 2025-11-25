from pathlib import Path


def dump_mesh(path, gmsh_mesh_str):
    if not gmsh_mesh_str:
        return
    with Path("mesh.msh").open("wt", newline="\n") as fh:
        fh.write(gmsh_mesh_str)
