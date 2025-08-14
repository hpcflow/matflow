from pathlib import Path
from textwrap import dedent, indent
import numpy as np


def write_block_mesh_file(path, volume_element, VE_origin, boundary):
    """

    References
    ----------
    [1] https://www.openfoam.com/documentation/user-guide/4-mesh-generation-and-conversion/4.3-mesh-generation-with-the-blockmesh-utility

    """
    TEMPLATE = dedent(
        """\
        /*--------------------------------*- C++ -*----------------------------------*\\
        | =========                 |                                                 |
        | \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
        |  \\\\    /   O peration     | Version:  3.10                                  |
        |   \\\\  /    A nd           | Web:      www.OpenFOAM.org                      |
        |    \\\\/     M anipulation  |                                                 |
        \\*---------------------------------------------------------------------------*/
        FoamFile
        {{
            version     2.0;
            format      ascii;
            class       dictionary;
            object      blockMeshDict;
        }}
        // * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

        convertToMeters 1e-3;

        vertices
        (
        {box_vertices}
        );

        blocks
        (
            hex (0 1 2 3 4 5 6 7) ({num_cells}) simpleGrading (1 1 1)		//REGION 1
        );

        edges
        (
        );

        boundary
        (
        {boundary}
        );

        mergePatchPairs
        (

        );

        // ************************************************************************* //

    """
    )

    BOUNDARY_PATCH_TEMPLATE = dedent(
        """\
    {patch_name}
    {{
        type {patch_type};
        faces
        (
    {vertices_str}
        );
    }}
    """
    )

    INDENT = "    "

    # as described in [1]:
    VERTS_LOOKUP = {
        "+x1": (1, 2, 6, 5),
        "+x2": (3, 7, 6, 2),
        "+x3": (5, 6, 7, 4),
        "-x1": (0, 4, 7, 3),
        "-x2": (1, 5, 4, 0),
        "-x3": (0, 3, 2, 1),
    }
    VERTS_LOOKUP["x1"] = VERTS_LOOKUP["+x1"]
    VERTS_LOOKUP["x2"] = VERTS_LOOKUP["+x2"]
    VERTS_LOOKUP["x3"] = VERTS_LOOKUP["+x3"]

    grid_size = volume_element["grid_size"][:]
    size = volume_element["size"]
    box = np.eye(3) * np.array(size)  # shape: (3, 3)
    origin = np.asarray(VE_origin)  # shape: (3)
    corners = get_box_corners(box=box, origin=origin).T

    box_verts = []
    for idx, vert in enumerate(corners):
        vert_str = " ".join(str(vert_i) for vert_i in vert)
        box_verts.append(f"({vert_str}) // {idx}")

    boundary_lst = []
    for bound in boundary:
        boundary_lst.append(
            BOUNDARY_PATCH_TEMPLATE.format(
                patch_name=bound["patch_name"],
                patch_type=bound["type"],
                vertices_str=indent(
                    "\n".join(
                        "(" + " ".join(str(i) for i in VERTS_LOOKUP[norm.lower()]) + ")"
                        for norm in bound["face_normals"]
                    ),
                    2 * INDENT,
                ),
            )
        )

    with path.open("wt") as fp:
        fp.write(
            TEMPLATE.format(
                box_vertices=indent("\n".join(box_verts), INDENT),
                num_cells=" ".join(str(gs_i) for gs_i in grid_size),
                boundary=indent("\n".join(boundary_lst), INDENT),
            )
        )


def get_box_corners(box, origin=None):
    """
    Get all eight corners of a parallelepiped defined by three edge vectors and an origin
    vector.

    Parameters
    ----------
    box : ndarray of shape  (3, 3)
        Array defining a the edges of a parallelepiped as three 3D column vectors.
    origin : ndarray of shape (3), optional
        Array defining the origin of the parallelepiped.

    Returns
    -------
    ndarray of shape (3, 8)
        Returns eight 3D column vectors which describe the corners of the parallelepiped.
        Corners are ordered as per OpenFOAM's blockMesh mesh-generation utility [1].

    References
    ----------
    [1] https://www.openfoam.com/documentation/user-guide/4-mesh-generation-and-conversion/4.3-mesh-generation-with-the-blockmesh-utility

    Examples
    --------
    >>> edges = np.random.randint(-1, 4, (3, 3))
    >>> edges
    array([[ 1, -1,  1],
           [ 2,  3,  1],
           [-1,  0,  3]], dtype=int32)
    >>> geometry.get_box_corners(a)
    array([[ 0,  1,  0, -1,  1,  2,  1,  0],
           [ 0,  2,  5,  3,  1,  3,  6,  4],
           [ 0, -1, -1,  0,  3,  2,  2,  3]], dtype=int32)

    """

    if origin is None:
        origin = np.zeros(3, dtype=box.dtype)

    corners = np.zeros((3, 8), dtype=box.dtype)  # 0: 0
    corners[:, 1] = box[:, 0]  # 1: x_1
    corners[:, 2] = box[:, 0] + box[:, 1]  # 2: x_1 + x_2
    corners[:, 3] = box[:, 1]  # 3: x_2
    corners[:, 4] = box[:, 2]  # 4: x_3
    corners[:, 5] = box[:, 0] + box[:, 2]  # 5: x_1 + x_3
    corners[:, 6] = box[:, 0] + box[:, 1] + box[:, 2]  # 6: x_1 + x_2 + x_3
    corners[:, 7] = box[:, 1] + box[:, 2]  # 7: x_2 + x_3

    corners += origin[None].T

    return corners
