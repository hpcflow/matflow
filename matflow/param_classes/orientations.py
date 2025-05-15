"""
Crystal orientation information.
"""

from __future__ import annotations
from dataclasses import dataclass
import enum
from pathlib import Path
from typing_extensions import Any, ClassVar, Self, TypeGuard

import numpy as np
from numpy.typing import NDArray, ArrayLike
import zarr
from hpcflow.sdk.core.parameters import ParameterValue
from hpcflow.sdk.core.utils import get_enum_by_name_or_val
from matflow.param_classes.utils import read_numeric_csv_file


@dataclass
class _EulerDefinition:
    _value: int
    #: The order to apply Euler rotations.
    rotation_order: str
    __doc__: str


class EulerDefinition(_EulerDefinition, enum.Enum):
    """
    How to apply Euler angles.
    """

    #: Convention typically used in crystallography.
    BUNGE = (0, "ZXZ", "Convention typically used in crystallography.")

    @property
    def value(self) -> int:
        """
        The index of the enumeration value.
        """
        return self._value


class QuatOrder(enum.Enum):
    """Order in which the four quaternion components are listed.

    Dream3D [1] uses vector-scalar ordering, whereas most other programs seem to use
    scalar-vector ordering.

    References
    ----------
    [1] http://dream3d.bluequartz.net/Help/Filters/OrientationAnalysisFilters/ConvertQuaternion/

    """

    #: Scalar first.
    SCALAR_VECTOR = 0
    #: Vector first.
    VECTOR_SCALAR = 1


class OrientationRepresentationType(enum.Enum):
    """
    How the orientation is represented.
    """

    #: Representation is a quaternion.
    QUATERNION = 0
    #: Representation is by Euler angles.
    EULER = 1


@dataclass
class OrientationRepresentation(ParameterValue):
    """
    A representation descriptor of an orientation.

    Parameters
    ----------
    type
        How the orientation is represented.
    euler_definition
        For Euler angles, how the angles are applied.
    euler_is_degrees
        For Euler angles, whether the angles are in degrees or radians.
    quat_order
        For quaternions, what is the order of the scalar wrt the vector.
    """

    #: How the orientation is represented.
    type: OrientationRepresentationType
    #: For Euler angles, how the angles are applied.
    euler_definition: EulerDefinition | None = None
    #: For Euler angles, whether the angles are in degrees or radians.
    euler_is_degrees: bool | None = None
    #: For quaternions, what is the order of the scalar wrt the vector.
    quat_order: QuatOrder | None = None

    def __post_init__(self):
        self.type = get_enum_by_name_or_val(OrientationRepresentationType, self.type)
        if self.type is OrientationRepresentationType.EULER:
            if self.euler_definition is None:
                raise ValueError("Must specify `euler_definition`.")
            if self.euler_is_degrees is None:
                raise ValueError("Must specify `euler_is_degrees`.")
        elif self.type is OrientationRepresentationType.QUATERNION:
            if self.quat_order is None:
                raise ValueError("Must specify `quat_order`.")
        self.euler_definition = get_enum_by_name_or_val(
            EulerDefinition, self.euler_definition
        )
        self.quat_order = get_enum_by_name_or_val(QuatOrder, self.quat_order)

    @classmethod
    def euler(
        cls, is_degrees: bool = False, definition: EulerDefinition = EulerDefinition.BUNGE
    ) -> Self:
        """
        Make a representation of an orientation that uses Euler angles.

        Parameters
        ----------
        is_degrees
            Whether the angles are in degrees or radians.
        definition
            How the angles are applied.
        """
        return cls(OrientationRepresentationType.EULER, definition, is_degrees)

    @classmethod
    def quaternion(cls, order: QuatOrder = QuatOrder.SCALAR_VECTOR) -> Self:
        """
        Make a representation of an orientation that uses quaternions.

        Parameters
        ----------
        order
            What is the order of the scalar wrt the vector.
        """
        return cls(OrientationRepresentationType.QUATERNION, quat_order=order)


class LatticeDirection(enum.Enum):
    """
    Lattice directions for unit cells.
    """

    #: Real-space A.
    A = 0
    #: Real-space B.
    B = 1
    #: Real-space C.
    C = 2

    #: Reciprocal-space A*.
    A_STAR = 3
    #: Reciprocal-space B*.
    B_STAR = 4
    #: Reciprocal-space C*.
    C_STAR = 5


@dataclass
class UnitCellAlignment(ParameterValue):
    """
    A description of the alignment of a unit cell.

    Parameters
    ----------
    x: str | LatticeDirection
        The direction of the X component.
    y: str | LatticeDirection
        The direction of the Y component.
    z: str | LatticeDirection
        The direction of the Z component.
    """

    _typ: ClassVar[str] = "unit_cell_alignment"

    #: The direction of the X component.
    x: LatticeDirection | None = None
    #: The direction of the Y component.
    y: LatticeDirection | None = None
    #: The direction of the Z component.
    z: LatticeDirection | None = None

    def __post_init__(self):
        self.x = get_enum_by_name_or_val(LatticeDirection, self.x)
        self.y = get_enum_by_name_or_val(LatticeDirection, self.y)
        self.z = get_enum_by_name_or_val(LatticeDirection, self.z)

    @classmethod
    def from_hex_convention_DAMASK(cls) -> Self:
        """
        Generate a unit cell alignment from Damask's default convention for hexagonal
        symmetry.
        """
        # TODO: check!
        return cls(x=LatticeDirection.A, y=LatticeDirection.B_STAR, z=LatticeDirection.C)

    @classmethod
    def from_hex_convention_MTEX(cls) -> Self:
        """Generate a unit cell alignment from MTEX's default convention for hexagonal
        symmetry.

        Tested using this command in MTEX: `crystalSymmetry("hexagonal").alignment`
        """
        return cls(
            x=LatticeDirection.A_STAR,
            y=LatticeDirection.B,
            z=LatticeDirection.C_STAR,
        )


@dataclass
class Orientations(ParameterValue):
    """
    A description of the orientations of some data.

    Parameters
    ----------
    data
        The orientation data.
    unit_cell_alignment
        The alignment of the unit cell.
    representation
        The orientation representation descriptor.
    """

    _typ: ClassVar[str] = "orientations"

    #: Orientation data
    data: NDArray
    #: Alignment of the unit cell.
    unit_cell_alignment: UnitCellAlignment
    #: How the orientation data is represented.
    representation: OrientationRepresentation

    @staticmethod
    def __is_dict(value) -> TypeGuard[dict[str, Any]]:
        # TypeGuard, not TypeIs; gets the correct type semantics
        return isinstance(value, dict)

    @staticmethod
    def __is_just_array_like(value: ArrayLike) -> TypeGuard[list]:
        # TypeGuard, not TypeIs; gets the correct type semantics
        # Type should really be "array like that isn't an ndarray" but that's
        # horrible to express.
        return not isinstance(value, np.ndarray)

    def __post_init__(self) -> None:
        if self.__is_just_array_like(self.data):
            self.data = np.asarray(self.data)
        if self.__is_dict(self.representation):
            self.representation = OrientationRepresentation(**self.representation)
        if self.__is_dict(self.unit_cell_alignment):
            self.unit_cell_alignment = UnitCellAlignment(**self.unit_cell_alignment)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.data.shape == other.data.shape
            and np.allclose(self.data, other.data)
            and self.unit_cell_alignment == other.unit_cell_alignment
            and self.representation == other.representation
        )

    @classmethod
    def save_from_HDF5_group(cls, group, param_id: int, workflow):
        """Save orientation data from an HDF5 group to a persistent workflow.

        Note
        ----
        We avoid loading the data into memory all at once by firstly generating an
        `Orientations` object with a small data array, and then copying from the HDF5
        group directly into the newly created Zarr group.

        We assume that the workflow is using a Zarr datastore. This is not checked!
        """

        repr_type = int(group.attrs.get("representation_type")[0])
        repr_quat_order = int(group.attrs.get("representation_quat_order")[0])
        obj = cls(
            data=np.array([0]),
            representation=OrientationRepresentation(
                type=repr_type,
                quat_order=repr_quat_order,
            ),
            unit_cell_alignment=dict(
                zip(("x", "y", "z"), group.attrs.get("unit_cell_alignment"))
            ),
        )
        workflow.set_parameter_value(param_id=param_id, value=obj, commit=True)

        # now replace placeholder data with correct data:
        zarr_grp, dataset_name = workflow._store._get_array_group_and_dataset(
            mode="r+",
            param_id=param_id,
            data_path=["data"],
        )
        zarr.copy(
            source=group["data"],
            dest=zarr_grp,
            name=dataset_name,
            if_exists="replace",
        )

    def dump_to_HDF5_group(self, group):
        group.create_dataset("data", data=np.asarray(self.data))
        group.attrs["representation_type"] = self.representation.type.value
        group.attrs["representation_quat_order"] = self.representation.quat_order.value
        group.attrs["unit_cell_alignment"] = [
            self.unit_cell_alignment.x.value,
            self.unit_cell_alignment.y.value,
            self.unit_cell_alignment.z.value,
        ]

    @classmethod
    def dump_element_group_to_HDF5_group(cls, objs: list[Orientations], group):
        # merge all orientation data into one array, and assume all metadata is the same
        # for all objects:
        first = objs[0]
        group.create_dataset("data", data=np.vstack([np.asarray(i.data) for i in objs]))
        group.attrs["representation_type"] = first.representation.type.value
        group.attrs["representation_quat_order"] = first.representation.quat_order.value
        group.attrs["unit_cell_alignment"] = [
            first.unit_cell_alignment.x.value,
            first.unit_cell_alignment.y.value,
            first.unit_cell_alignment.z.value,
        ]
        group.attrs["number_of_orientation_sets"] = len(objs)

    @classmethod
    def from_JSON_like(cls, data: ArrayLike, ori_format: str) -> Self:
        """For custom initialisation via YAML or JSON."""
        if ori_format.lower() in ("quaternion", "quaternions"):
            ori = OrientationRepresentation.quaternion()
        elif ori_format.lower() == "euler":
            ori = OrientationRepresentation.euler()
        else:
            raise ValueError("unsupported orientation format")

        return cls(
            data=np.asarray(data),
            unit_cell_alignment=UnitCellAlignment.from_hex_convention_DAMASK(),
            representation=ori,
        )

    @classmethod
    def from_random(cls, number: int) -> Self:
        """
        Generate random orientation data.

        Parameters
        ----------
        number
            The number of orientations to generate.
        """
        return cls(
            data=cls.quat_sample_random(number),
            unit_cell_alignment=UnitCellAlignment.from_hex_convention_DAMASK(),
            representation=OrientationRepresentation.quaternion(),
        )

    @classmethod
    def from_file(
        cls,
        path: str,
        representation: dict,
        unit_cell_alignment: UnitCellAlignment,
        *,
        number: int | None = None,
        start_index: int = 0,
        delimiter: str = " ",
        columns: list[int] | None = None,
    ) -> Self:
        """
        Load orientation data from a text file.

        Parameters
        ----------
        path
            Path to the file to load from.
        representation
            Description of how the orientation data is arranged.
        unit_cell_alignment
            How the unit cell is aligned.
        number
            Number of orientations to read from the file.
        start_index
            The line number of the file that the orientations start at.
            Allows skipping headers.
        delimiter
            The delimiter separating values in the file.
            Defaults to space, but commas and tabs are also sensible
            (and correspond to CSV and TSV files respectively).
        columns
            The columns in the file to read from.
            Defaults to reading every column.
        """
        exc_message = "Not enough orientations in the file."
        rep = OrientationRepresentation(**representation)
        data = read_numeric_csv_file(
            path, number, start_index, delimiter, columns, exc_message
        )

        return cls(
            data=data,
            representation=rep,
            unit_cell_alignment=unit_cell_alignment,
        )

    @staticmethod
    def quat_sample_random(number: int) -> NDArray:
        """
        Generate random uniformly distributed unit quaternions.

        Parameters
        ----------
        number : int
            How many quaternions to generate.

        Returns
        -------
        quats : ndarray, shape (number, 4)

        References
        ----------
        https://stackoverflow.com/a/44031492/5042280
        http://planning.cs.uiuc.edu/node198.html
        """

        rand_nums = np.random.random((number, 3))
        return np.array(
            [
                np.sqrt(1 - rand_nums[:, 0]) * np.sin(2 * np.pi * rand_nums[:, 1]),
                np.sqrt(1 - rand_nums[:, 0]) * np.cos(2 * np.pi * rand_nums[:, 1]),
                np.sqrt(rand_nums[:, 0]) * np.sin(2 * np.pi * rand_nums[:, 2]),
                np.sqrt(rand_nums[:, 0]) * np.cos(2 * np.pi * rand_nums[:, 2]),
            ]
        ).T
