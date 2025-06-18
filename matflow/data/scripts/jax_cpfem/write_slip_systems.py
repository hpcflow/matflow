from textwrap import dedent


def write_slip_systems(path, slip_systems):
    # slip plane normals, followed by slip directions
    # FCC (?)

    # TEMPLATE = dedent(
    #     """\
    #     1 1 -1  0 1 1
    #     1 1 -1  1 0 1
    #     1 1 -1  1 -1  0
    #     1 -1  -1  0 1 -1
    #     1 -1  -1  1 0 1
    #     1 -1  -1  1 1 0
    #     1 -1  1 0 1 1
    #     1 -1  1 1 0 -1
    #     1 -1  1 1 1 0
    #     1 1 1 0 1 -1
    #     1 1 1 1 0 -1
    #     1 1 1 1 -1  0
    # """
    # )
    with path.open("wt") as fh:
        for slip_plane, slip_dir in slip_systems:
            fh.write(" ".join(str(i) for i in [*slip_plane, *slip_dir]) + "\n")
