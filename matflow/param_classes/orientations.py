from dataclasses import dataclass
import enum
from pathlib import Path
from typing import Optional

import numpy as np
import zarr
from hpcflow.sdk.core.parameters import ParameterValue
from hpcflow.sdk.core.utils import get_enum_by_name_or_val


class EulerDefinition(enum.Enum):
    def __new__(cls, value, rotation_order, doc=None):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.rotation_order = rotation_order
        obj.__doc__ = doc
        return obj

    BUNGE = (0, "ZXZ", "Convention typically used in crystallography.")


class QuatOrder(enum.Enum):
    """Order in which the four quaternion components listed.

    Dream3D [1] uses vector-scalar ordering, whereas most other programs seem to use
    scalar-vector ordering.

    References
    ----------
    [1] http://dream3d.bluequartz.net/Help/Filters/OrientationAnalysisFilters/ConvertQuaternion/

    """

    SCALAR_VECTOR = 0
    VECTOR_SCALAR = 1


class OrientationRepresentationType(enum.Enum):
    QUATERNION = 0
    EULER = 1


@dataclass
class OrientationRepresentation(ParameterValue):
    type: OrientationRepresentationType
    euler_definition: Optional[EulerDefinition] = None
    euler_is_degrees: Optional[bool] = None
    quat_order: Optional[QuatOrder] = None

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


class LatticeDirection(enum.Enum):
    # real-space directions:
    A = 0
    B = 1
    C = 2

    # reciprocal-space directions
    A_STAR = 3
    B_STAR = 4
    C_STAR = 5


@dataclass
class UnitCellAlignment(ParameterValue):
    _typ = "unit_cell_alignment"

    x: Optional[LatticeDirection] = None
    y: Optional[LatticeDirection] = None
    z: Optional[LatticeDirection] = None

    def __post_init__(self):
        self.x = get_enum_by_name_or_val(LatticeDirection, self.x)
        self.y = get_enum_by_name_or_val(LatticeDirection, self.y)
        self.z = get_enum_by_name_or_val(LatticeDirection, self.z)

    @classmethod
    def from_hex_convention_DAMASK(cls):
        # TODO: check!
        return cls(x=LatticeDirection.A, y=LatticeDirection.B_STAR, z=LatticeDirection.C)

    @classmethod
    def from_hex_convention_MTEX(cls):
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
    _typ = "orientations"

    data: np.ndarray
    unit_cell_alignment: UnitCellAlignment
    representation: OrientationRepresentation

    def __post_init__(self):
        self.data = np.asarray(self.data)

        if not isinstance(self.representation, OrientationRepresentation):
            self.representation = OrientationRepresentation(**self.representation)

        if not isinstance(self.unit_cell_alignment, UnitCellAlignment):
            self.unit_cell_alignment = UnitCellAlignment(**self.unit_cell_alignment)

    def __eq__(self, other: object) -> bool:
        if (
            isinstance(other, self.__class__)
            and self.data.shape == other.data.shape
            and np.allclose(self.data, other.data)
            and self.unit_cell_alignment == other.unit_cell_alignment
            and self.representation == other.representation
        ):
            return True
        return False

    @classmethod
    def save_from_HDF5_group(cls, group, param_id: int, workflow):
        """Save orientation data from an HDF5 group to a persistent workflow.

        We avoid loading the data into memory all at once by firstly generating an
        `Orientations` object with a small data array, and then copying from the HDF5
        group directly into the newly created Zarr group.

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
    def from_JSON_like(cls, data, ori_format):
        """For custom initialisation via YAML or JSON."""
        return cls(data=np.asarray(data), ori_format=ori_format)

    @classmethod
    def from_random(cls, number):
        return cls(
            data=cls.quat_sample_random(number),
            unit_cell_alignment=UnitCellAlignment.from_hex_convention_DAMASK(),
            representation=OrientationRepresentation(
                type=OrientationRepresentationType.QUATERNION,
                quat_order=QuatOrder.SCALAR_VECTOR,
            ),
        )

    @classmethod
    def from_file(
        cls,
        path,
        representation,
        unit_cell_alignment,
        number=None,
        start_index=0,
        delimiter=" ",
    ):
        rep = OrientationRepresentation(**representation)
        data = []
        with Path(path).open("rt") as fh:
            for idx, line in enumerate(fh):
                line = line.strip()
                if not line or idx < start_index:
                    continue
                elif len(data) < number if number is not None else True:
                    data.append([float(i) for i in line.split(delimiter)])
        if number is not None and len(data) < number:
            raise ValueError("Not enough orientations in the file.")

        return cls(
            data=np.asarray(data),
            representation=rep,
            unit_cell_alignment=unit_cell_alignment,
        )

    @staticmethod
    def quat_sample_random(number):
        """Generate random uniformly distributed unit quaternions.

        Parameters
        ----------
        number : int
            How many quaternions to generate.

        Returns
        -------
        quats : ndarray of shape (number, 4)

        References
        ----------
        https://stackoverflow.com/a/44031492/5042280
        http://planning.cs.uiuc.edu/node198.html
        """

        rand_nums = np.random.random((number, 3))
        quats = np.array(
            [
                np.sqrt(1 - rand_nums[:, 0]) * np.sin(2 * np.pi * rand_nums[:, 1]),
                np.sqrt(1 - rand_nums[:, 0]) * np.cos(2 * np.pi * rand_nums[:, 1]),
                np.sqrt(rand_nums[:, 0]) * np.sin(2 * np.pi * rand_nums[:, 2]),
                np.sqrt(rand_nums[:, 0]) * np.cos(2 * np.pi * rand_nums[:, 2]),
            ]
        ).T

        return quats
