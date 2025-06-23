"""
A boundary condition class to represent some types of load case in a way amenable to the
JAX-CPFEM crystal plasticity code. This is not a `ParameterValue` sub-class, but rather a
helper class.

"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal
from textwrap import dedent

from typing_extensions import Final, Self


class BoundaryCondition:
    """Simple boundary conditions container that can be used to represent a subset of
    particular load cases, as corners or faces of a unit box, and the value that should be
    applied within those regions.

    Parameters
    ----------
    corners
        Corners of the 3D box for which boundary condition should apply. Each corner
        should be specified as a three-tuple of 0s or 1s. For example `(0, 0, 0)`
        corresponds to the box origin, and `(0, 1, 1)` corresponds to the `x=0`, `y=1`,
        `z=1` corner. Specify either `corners` or `faces`.
    faces
        A sequence of strings, where each string identifies the normal direction of a
        specified box face, when viewed from the middle of the box. For example, the `+z`
        direction corresponds to the `z=1` face, and the `-x` direction corresponds to the
        `x=0` face. Specify either `corners` or `faces`.
    value
        A value for one or more of the "x", "y", and "z" components of the field. This can
        be specified as a number or a string label that has some application-dependent
        meaning.

    """

    _DIRS: Final[tuple[str, ...]] = ("x", "y", "z")

    _JAX_CPFEM_BC_FUNC_CORNER_MAP = {
        (0, 0, 0): "corner_0",
        (1, 0, 0): "corner_1",
        (1, 1, 0): "corner_2",
        (0, 1, 0): "corner_3",
        (0, 0, 1): "corner_4",
        (1, 0, 1): "corner_5",
        (1, 1, 1): "corner_6",
        (0, 1, 1): "corner_7",
    }
    _JAX_CPFEM_BC_FUNC_FACE_MAP = {
        "+x": "face_pos_x",
        "-x": "face_neg_x",
        "+y": "face_pos_y",
        "-y": "face_neg_y",
        "+z": "face_pos_z",
        "-z": "face_neg_z",
    }
    _LOCATION_FUNC_CORNER_BODY_TEMPLATE = (
        "return np.allclose(point, np.asarray({corner}), atol=1e-5)"
    )
    _LOCATION_FUNC_FACE_BODY_TEMPLATE = (
        "return np.isclose(point[{comp_idx}], {value}, atol=1e-5)"
    )

    def __init__(
        self,
        value: Mapping[Literal["x", "y", "z"], float | str],
        corners: (
            Sequence[Sequence[Literal[0, 1], Literal[0, 1], Literal[0, 1]]] | None
        ) = None,
        faces: Sequence[str] | None = None,
    ):
        if sum(i is not None for i in (corners, faces)) != 1:
            raise ValueError("Specify exactly one of `corners` and `faces`.")

        self.corners = corners
        self.faces = faces
        self.value = value

    def __repr__(self):
        region_name = "corners" if self.corners is not None else "faces"
        region = self.corners if self.corners is not None else self.faces
        return (
            f"{self.__class__.__name__}("
            f"{region_name}={region!r}, "
            f"value={self.value!r}"
            f")"
        )

    @classmethod
    def uniaxial(cls, direction: Literal["x", "y", "z"]) -> list[Self]:
        """Generate a list of boundary conditions that correspond to uniaxial loading
        along the specified direction."""
        non_axial_dirs = sorted(list(set(cls._DIRS).difference(direction)))
        return [
            cls(corners=([0, 0, 0],), value={non_axial_dirs[0]: 0, non_axial_dirs[1]: 0}),
            cls(faces=(f"-{direction}",), value={direction: 0}),
            cls(faces=(f"+{direction}",), value={direction: "u(t)"}),
        ]

    @classmethod
    def one_dimensional(cls, direction: Literal["x", "y", "z"]) -> list[Self]:
        """Generate a list of boundary conditions that correspond to one-dimensional
        loading along the specified direction (no deformation in non-axial directions)."""
        non_axial_dirs = sorted(list(set(cls._DIRS).difference(direction)))
        return [
            cls(faces=(f"-{direction}",), value={"x": 0, "y": 0, "z": 0}),
            cls(
                faces=(f"+{direction}",),
                value={non_axial_dirs[0]: 0, non_axial_dirs[1]: 0, direction: "u(t)"},
            ),
        ]

    @staticmethod
    def get_corner_location_func_str(corner) -> str:
        """Generate Python code that defines a function that return True if the provided
        3D point is located at the specified corner, and False otherwise.

        Notes
        -----
        The generated code is used as part of the problem definition script when running a
        JAX-CPFEM simulation.

        """
        func_str = dedent(
            """\
        def {func_name}(point):
            {func_body}

        """
        ).format(
            func_name=BoundaryCondition._JAX_CPFEM_BC_FUNC_CORNER_MAP[tuple(corner)],
            func_body=BoundaryCondition._LOCATION_FUNC_CORNER_BODY_TEMPLATE.format(
                corner=f"[{', '.join(str(i) for i in corner)}]"
            ),
        )
        return func_str

    @staticmethod
    def get_face_location_func_str(face, domain_size) -> str:
        """Generate Python code that defines a function that return True if the provided
        3D point is located within the specified plane (see the `BoundaryCondition.faces`
        documentation for specification details), and False otherwise.

        Notes
        -----
        The generated code is used as part of the problem definition script when running a
        JAX-CPFEM simulation.

        """
        face = face.lower()
        if len(face) == 1:
            face = f"+{face}"
        sign, dir = face

        comp_idx = BoundaryCondition._DIRS.index(dir)
        func_str = dedent(
            """\
        def {func_name}(point):
            {func_body}

        """
        ).format(
            func_name=BoundaryCondition._JAX_CPFEM_BC_FUNC_FACE_MAP[face],
            func_body=BoundaryCondition._LOCATION_FUNC_FACE_BODY_TEMPLATE.format(
                comp_idx=comp_idx,
                value=domain_size[comp_idx] if sign == "+" else 0,
            ),
        )
        return func_str
