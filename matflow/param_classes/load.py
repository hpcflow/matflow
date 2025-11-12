"""
Loadings to apply to a simulated sample.
"""

from __future__ import annotations
from collections.abc import Callable, Iterator
import copy
from dataclasses import dataclass
import enum

import logging
from typing import Any, cast
from typing_extensions import ClassVar, Final, Self

import numpy as np
from numpy.typing import ArrayLike
from hpcflow.sdk.core.parameters import ParameterValue
from hpcflow.sdk.core.utils import get_enum_by_name_or_val

import matflow as mf
from matflow.param_classes.utils import masked_array_from_list

logger = logging.getLogger(__name__)


@dataclass
class _StrainRateMode:
    """
    Model of the state of a :py:class:`StrainRateMode`.
    """

    _value: int
    #: Symbol associated with this mode.
    symbol: str
    __doc__: str


class StrainRateMode(_StrainRateMode, enum.Enum):
    """
    The mode of the strain rate.
    """

    #: Deformation gradient rate.
    DEF_GRAD_RATE = (0, "F_rate", "Deformation gradient rate.")
    #: Velocity gradient.
    VEL_GRAD = (1, "L", "Velocity gradient.")
    #: Velocity gradient approximation.
    VEL_GRAD_APPROX = (2, "L_approx", "Velocity gradient approximation.")

    @property
    def value(self) -> int:
        """
        The index value of this enumeration element.
        """
        return self._value


class LoadStep(ParameterValue):
    """Boundary conditions for volume element loading.

    Parameters
    ----------
    total_time : float | int
        Total simulation time.
    num_increments
        Number of simulation increments.
    direction
        Direction or directions in which loading is done.
    normal_direction
        Direction of normal vector.
    target_def_grad : numpy.ma.core.MaskedArray, shape (3, 3)
        Deformation gradient aim tensor. Masked values correspond to unmasked values in
        `stress`.
    target_def_grad_rate : numpy.ma.core.MaskedArray, shape (3, 3)
        Deformation gradient rate tensor. Masked values correspond to unmasked values in
        `stress`.
    target_vel_grad : numpy.ma.core.MaskedArray, shape (3, 3)
        Velocity gradient aim tensor.
    stress : numpy.ma.core.MaskedArray, shape (3, 3)
        Stress tensor. Masked values correspond to unmasked values in
        `target_def_grad` or `target_def_grad_rate`.
    dump_frequency : int
        By default, 1, meaning results are written out every increment.
    """

    _DIR_IDX: Final[tuple[str, ...]] = ("x", "y", "z")

    def __init__(
        self,
        total_time: float,
        num_increments: int,
        direction: str | None = None,
        normal_direction: str | None = None,
        target_def_grad: ArrayLike | None = None,
        target_def_grad_rate: ArrayLike | None = None,
        target_vel_grad: ArrayLike | None = None,
        stress: ArrayLike | None = None,
        dump_frequency: int = 1,
    ) -> None:
        #: Total simulation time.
        self.total_time = total_time
        #: Number of simulation increments.
        self.num_increments = num_increments
        #: Direction or directions in which loading is done.
        self.direction = direction
        #: Direction of normal vector.
        self.normal_direction = normal_direction
        #: Deformation gradient aim tensor.
        self.target_def_grad = target_def_grad
        #: Deformation gradient rate tensor.
        self.target_def_grad_rate = target_def_grad_rate
        #: Velocity gradient aim tensor.
        self.target_vel_grad = target_vel_grad
        #: Stress tensor.
        self.stress = stress
        #: How frequently results are written out; the number of steps per dump.
        self.dump_frequency = dump_frequency

        # assigned if constructed via a helper class method:
        self._method_name: str | None = None
        self._method_args: dict[str, Any] | None = None

        self._validate()

    @staticmethod
    def __cmp_tensors(mine: ArrayLike | None, theirs: ArrayLike | None):
        if mine is None:
            return theirs is None
        return theirs is not None and np.allclose(mine, theirs)

    def __eq__(self, other: object) -> bool:
        # check type and scalars
        if not (
            isinstance(other, self.__class__)
            and self.total_time == other.total_time
            and self.num_increments == other.num_increments
            and self.direction == other.direction
            and self.normal_direction == other.normal_direction
            and self.dump_frequency == other.dump_frequency
        ):
            return False

        # check tensors
        if not self.__cmp_tensors(self.stress, other.stress):
            return False
        if not self.__cmp_tensors(self.target_def_grad, other.target_def_grad):
            return False
        if not self.__cmp_tensors(self.target_def_grad_rate, other.target_def_grad_rate):
            return False
        if not self.__cmp_tensors(self.target_vel_grad, other.target_vel_grad):
            return False

        return True

    def _validate(self):
        if self.strain_like_tensor is None and self.stress is None:
            raise ValueError(
                "Specify a strain-like tensor (`target_def_grad`, `target_def_grad_rate`,"
                " `target_vel_grad`) and/or the `stress` tensor."
            )
        if isinstance(self.target_def_grad, list):
            self.target_def_grad = masked_array_from_list(self.target_def_grad)

        if isinstance(self.target_def_grad_rate, list):
            self.target_def_grad_rate = masked_array_from_list(self.target_def_grad_rate)

        if isinstance(self.target_vel_grad, list):
            self.target_vel_grad = masked_array_from_list(self.target_vel_grad)

        if self.stress is not None:
            if isinstance(self.stress, list):
                self.stress = masked_array_from_list(self.stress)
            xor_arr = np.logical_xor(self.strain_like_tensor.mask, self.stress.mask)
            if not np.all(xor_arr):
                raise RuntimeError(
                    "Stress and strain tensor masks should be element-wise mutually "
                    "exclusive, but they are not."
                )

    def _remember_name_args(self, name: str | None, args: dict[str, Any]) -> Self:
        self._method_name, self._method_args = name, args
        return self

    @property
    def strain_like_tensor(self) -> ArrayLike | None:
        """
        The strain-like tensor, if known.
        """
        if self.target_def_grad is not None:
            return self.target_def_grad
        elif self.target_def_grad_rate is not None:
            return self.target_def_grad_rate
        elif self.target_vel_grad is not None:
            return self.target_vel_grad
        return None

    @property
    def method_name(self) -> str | None:
        """
        The name of the factory method used to make this loading step, if known.
        If `None`, new instances like this one should be made directly.
        """
        return self._method_name

    @property
    def method_args(self) -> dict[str, Any]:
        """
        The arguments to the factory method used to make this loading step, if known.
        """
        return self._method_args or {}

    @property
    def type(self) -> str:
        """More user-friendly access to method name."""
        return self._method_name or self.__class__.__name__

    @property
    def strain(self) -> float | None:
        """
        For a limited subset of load step types (e.g. uniaxial), return the scalar target
        strain.
        """
        if self.type in ("uniaxial",):
            return self.method_args["target_strain"]

    @property
    def strain_rate(self) -> float | None:
        """
        For a limited subset of load step types (e.g. uniaxial), return the scalar target
        strain rate.
        """
        if self.type in ("uniaxial",):
            return self.method_args["target_strain_rate"]

    def __repr__(self) -> str:
        type_str = f"type={self.type!r}, " if self.type else ""
        if self.direction:
            dir_str = f", direction={self.direction!r}"
        elif self.normal_direction:
            dir_str = f", normal_direction={self.normal_direction!r}"
        else:
            dir_str = ""
        return (
            f"{self.__class__.__name__}({type_str}"
            f"num_increments={self.num_increments}, "
            f"total_time={self.total_time}{dir_str}"
            f")"
        )

    @classmethod
    def example_uniaxial(cls) -> Self:
        """
        A non-parametrisable example uniaxial load step.
        """
        time = 100
        incs = 200
        direction = "x"
        rate = 1e-3
        mf.logger.debug(  # demonstration of logging in a `ParameterValue` class
            f"Generating an example uniaxial load step with parameters: time={time!r}, "
            f"num_increments={incs!r}, direction={direction!r}, "
            f"target_def_grad_rate={rate!r}."
        )
        return cls.uniaxial(
            total_time=time,
            num_increments=incs,
            direction=direction,
            target_def_grad_rate=rate,
        )

    @classmethod
    def uniaxial(
        cls,
        total_time: float | int,
        num_increments: int,
        direction: str,
        target_strain: float | None = None,
        target_strain_rate: float | None = None,
        target_def_grad_rate: float | None = None,
        target_def_grad: float | None = None,
        dump_frequency: int = 1,
    ) -> Self:
        """
        Generate a uniaxial load step.

        Parameters
        ----------
        total_time
            Total simulation time.
        num_increments
            Number of simulation increments.
        direction : str
            A single character, "x", "y" or "z", representing the loading direction.
        target_def_grad : float
            Target deformation gradient to achieve along the loading direction component.
        target_strain: float
            Target engineering strain to achieve along the loading direction. Specify at
            most one of `target_strain` and `target_def_grad`.
        target_def_grad_rate : float
            Target deformation gradient rate to achieve along the loading direction
            component.
        target_strain_rate: float
            Target engineering strain rate to achieve along the loading direction. Specify
            at most one of `target_strain_rate` and `target_def_grad_rate`.
        dump_frequency : int, optional
            By default, 1, meaning results are written out every increment.
        """

        _method_name = "uniaxial"
        _method_args = {
            "total_time": total_time,
            "num_increments": num_increments,
            "direction": direction,
            "target_strain": target_strain,
            "target_strain_rate": target_strain_rate,
            "target_def_grad": target_def_grad,
            "target_def_grad_rate": target_def_grad_rate,
            "dump_frequency": dump_frequency,
        }

        # Validation:
        msg = (
            "Specify either `target_strain`, `target_strain_rate`, "
            "``target_def_grad` or target_def_grad_rate`."
        )
        strain_arg = (
            target_strain,
            target_strain_rate,
            target_def_grad,
            target_def_grad_rate,
        )
        if sum(s is not None for s in strain_arg) != 1:
            raise ValueError(msg)

        # convert strain (rate) to deformation gradient (rate) components, and ensure both
        # strain(_rate) and def_grad(_rate) are populated:
        if target_strain is not None:
            target_def_grad = 1 + target_strain
        elif target_def_grad is not None:
            target_strain = target_def_grad - 1

        if target_strain_rate is not None:
            target_def_grad_rate = target_strain_rate
        elif target_def_grad_rate is not None:
            target_strain_rate = target_def_grad_rate

        if target_def_grad_rate is not None:
            def_grad_val = target_def_grad_rate
        else:
            def_grad_val = target_def_grad

        try:
            loading_dir_idx = cls._DIR_IDX.index(direction)
        except ValueError:
            msg = (
                f'Loading direction "{direction}" not allowed. It should be one of "x", '
                f'"y" or "z".'
            )
            raise ValueError(msg)

        dg_arr = np.ma.masked_array(np.zeros((3, 3)), mask=np.eye(3))
        stress_arr = np.ma.masked_array(np.zeros((3, 3)), mask=np.logical_not(np.eye(3)))

        dg_arr[loading_dir_idx, loading_dir_idx] = def_grad_val
        dg_arr.mask[loading_dir_idx, loading_dir_idx] = False
        stress_arr.mask[loading_dir_idx, loading_dir_idx] = True

        def_grad_aim = dg_arr if target_def_grad is not None else None
        def_grad_rate = dg_arr if target_def_grad_rate is not None else None

        obj = cls(
            direction=direction,
            total_time=total_time,
            num_increments=num_increments,
            target_def_grad=def_grad_aim,
            target_def_grad_rate=def_grad_rate,
            stress=stress_arr,
            dump_frequency=dump_frequency,
        )
        return obj._remember_name_args(_method_name, _method_args)

    @classmethod
    def biaxial(
        cls,
        total_time: int | float,
        num_increments: int,
        direction: str,
        target_def_grad: float | None = None,
        target_def_grad_rate: float | None = None,
        dump_frequency: int = 1,
    ) -> Self:
        """
        Generate a biaxial load step.

        Parameters
        ----------
        total_time
            Total simulation time.
        num_increments
            Number of simulation increments.
        direction
            String of two characters, ij, where {i,j} ∈ {"x","y","z"}, corresponding to
            the two loading directions.
        target_def_grad
            Target deformation gradient to achieve along both loading direction
            components.
        target_def_grad_rate
            Target deformation gradient rate to achieve along both loading direction
            components.
        dump_frequency
            By default, 1, meaning results are written out every increment.
        """

        # TODO: this should be called `equibiaxial`?
        # How is this different from `2D_planar`?
        _method_name = "biaxial"
        _method_args = {
            "total_time": total_time,
            "num_increments": num_increments,
            "direction": direction,
            "target_def_grad_rate": target_def_grad_rate,
            "target_def_grad": target_def_grad,
            "dump_frequency": dump_frequency,
        }

        # Validation:
        msg = "Specify either `target_def_grad_rate` or `target_def_grad`."
        if all([t is None for t in [target_def_grad_rate, target_def_grad]]):
            raise ValueError(msg)
        if all([t is not None for t in [target_def_grad_rate, target_def_grad]]):
            raise ValueError(msg)

        if target_def_grad_rate is not None:
            def_grad_val = target_def_grad_rate
        else:
            def_grad_val = target_def_grad

        load_dir_idx: list[int] = []
        for load_dir in direction:
            try:
                load_dir_idx.append(cls._DIR_IDX.index(load_dir))
            except ValueError:
                raise ValueError(
                    f'Loading direction "{load_dir}" not allowed. '
                    f'Both loading directions should be one of "x", "y" or "z".'
                )

        zero_stress_dir = next(iter(set(cls._DIR_IDX).difference(direction)))
        zero_stress_dir_idx = cls._DIR_IDX.index(zero_stress_dir)

        dg_arr = np.ma.masked_array(np.zeros((3, 3)), mask=np.zeros((3, 3)))
        stress_arr = np.ma.masked_array(np.zeros((3, 3)), mask=np.ones((3, 3)))

        dg_arr[load_dir_idx, load_dir_idx] = def_grad_val
        dg_arr.mask[zero_stress_dir_idx, zero_stress_dir_idx] = True
        stress_arr.mask[zero_stress_dir_idx, zero_stress_dir_idx] = False

        def_grad = dg_arr if target_def_grad is not None else None
        def_grad_rate = dg_arr if target_def_grad_rate is not None else None

        obj = cls(
            direction=direction,
            total_time=total_time,
            num_increments=num_increments,
            target_def_grad=def_grad,
            target_def_grad_rate=def_grad_rate,
            stress=stress_arr,
            dump_frequency=dump_frequency,
        )
        return obj._remember_name_args(_method_name, _method_args)

    @classmethod
    def plane_strain(
        cls,
        total_time: int | float,
        num_increments: int,
        direction: str,
        target_def_grad: float | None = None,
        target_def_grad_rate: float | None = None,
        dump_frequency: int = 1,
        strain_rate_mode: StrainRateMode | str | None = None,
    ) -> Self:
        """
        Generate a plane-strain load step.

        Parameters
        ----------
        total_time
            Total simulation time.
        num_increments
            Number of simulation increments.
        direction
            String of two characters, ij, where {i,j} ∈ {"x","y","z"}. The first
            character, i, corresponds to the loading direction and the second, j,
            corresponds to the zero-strain direction. Zero stress will be specified on the
            remaining direction.
        target_def_grad
            Target deformation gradient to achieve along the loading direction component.
        target_def_grad_rate
            Target deformation gradient rate to achieve along the loading direction
            component.
        dump_frequency
            By default, 1, meaning results are written out every increment.
        strain_rate_mode
            One of "def_grad_rate", "vel_grad", "vel_grad_approx". If not specified,
            default is "def_grad_rate". Use "vel_grad_approx" for specifying non-mixed
            boundary conditions.
        """

        _method_name = "plane_strain"
        _method_args = {
            "total_time": total_time,
            "num_increments": num_increments,
            "direction": direction,
            "target_def_grad": target_def_grad,
            "target_def_grad_rate": target_def_grad_rate,
            "dump_frequency": dump_frequency,
            "strain_rate_mode": strain_rate_mode,
        }

        # Validation:
        msg = "Specify either `target_def_grad_rate` or `target_def_grad`."
        if all(t is None for t in [target_def_grad_rate, target_def_grad]):
            raise ValueError(msg)
        if all(t is not None for t in [target_def_grad_rate, target_def_grad]):
            raise ValueError(msg)

        if strain_rate_mode is None:
            mode = StrainRateMode.DEF_GRAD_RATE
        else:
            mode = get_enum_by_name_or_val(StrainRateMode, strain_rate_mode)

        if (
            mode in (StrainRateMode.VEL_GRAD, StrainRateMode.VEL_GRAD_APPROX)
            and target_def_grad_rate is None
        ):
            msg = (
                f"`target_def_grad_rate` must be specified for `strain_rate_mode` "
                f"{mode!r}"
            )
            raise ValueError(msg)

        if target_def_grad_rate is not None:
            def_grad_val = target_def_grad_rate
        else:
            def_grad_val = target_def_grad

        loading_dir, zero_strain_dir = direction
        try:
            loading_dir_idx = cls._DIR_IDX.index(loading_dir)
        except ValueError:
            msg = (
                f'Loading direction "{loading_dir}" not allowed. It should be one of '
                f'"x", "y" or "z".'
            )
            raise ValueError(msg)

        if zero_strain_dir not in cls._DIR_IDX:
            msg = (
                f'Zero-strain direction "{zero_strain_dir}" not allowed. It should be '
                f'one of "x", "y" or "z".'
            )
            raise ValueError(msg)

        zero_stress_dir = next(
            iter(set(cls._DIR_IDX).difference([loading_dir, zero_strain_dir]))
        )
        zero_stress_dir_idx = cls._DIR_IDX.index(zero_stress_dir)

        dg_arr = np.ma.masked_array(np.zeros((3, 3)), mask=np.zeros((3, 3)))
        stress_arr = np.ma.masked_array(np.zeros((3, 3)), mask=np.ones((3, 3)))

        dg_arr[loading_dir_idx, loading_dir_idx] = def_grad_val

        if mode is StrainRateMode.VEL_GRAD:
            # When using L with mixed BCs, each row must be either L or P:
            dg_arr.mask[zero_stress_dir_idx] = True
            stress_arr.mask[zero_stress_dir_idx] = False

        elif mode is StrainRateMode.VEL_GRAD_APPROX:
            dg_arr = dg_arr.data  # No need for a masked array
            # Without mixed BCs, we can get volume conservation with Trace(L) = 0:
            dg_arr[zero_stress_dir_idx, zero_stress_dir_idx] = -def_grad_val
            stress_arr = None

        elif mode is StrainRateMode.DEF_GRAD_RATE:
            dg_arr.mask[zero_stress_dir_idx, zero_stress_dir_idx] = True
            stress_arr.mask[zero_stress_dir_idx, zero_stress_dir_idx] = False

        if mode in (StrainRateMode.VEL_GRAD, StrainRateMode.VEL_GRAD_APPROX):
            def_grad = None
            def_grad_rate = None
            vel_grad = dg_arr
        else:
            def_grad = dg_arr if target_def_grad is not None else None
            def_grad_rate = dg_arr if target_def_grad_rate is not None else None
            vel_grad = None

        obj = cls(
            direction=direction,
            total_time=total_time,
            num_increments=num_increments,
            target_def_grad=def_grad,
            target_def_grad_rate=def_grad_rate,
            target_vel_grad=vel_grad,
            stress=stress_arr,
            dump_frequency=dump_frequency,
        )
        return obj._remember_name_args(_method_name, _method_args)

    @classmethod
    def planar_2D(
        cls,
        total_time: int | float,
        num_increments: int,
        normal_direction: str,
        target_def_grad: float | None = None,
        target_def_grad_rate: float | None = None,
        dump_frequency: int = 1,
    ) -> Self:
        """
        Generate a planar 2D load case normal to the x-, y-, or z-direction.

        Parameters
        ----------
        total_time
            Total simulation time.
        num_increments
            Number of simulation increments.
        normal_direction
            A single character, "x", "y" or "z", representing the loading plane normal
            direction.
        target_def_grad : (nested) list of float or ndarray of shape (2, 2)
            Target deformation gradient components. Either a 2D array, nested list, or a
            flat list. If passed as a flat list, the first and fourth elements correspond
            to the normal components of the deformation gradient tensor. The second
            element corresponds to the first-row, second-column (shear) component and the
            third element corresponds to the second-row, first-column (shear) component.
        target_def_grad_rate : (nested) list of float or ndarray of shape (2, 2)
            Target deformation gradient rate components. Either a 2D array, nested list,
            or a flat list. If passed as a flat list, the first and fourth elements
            correspond to the normal components of the deformation gradient rate tensor.
            The second element corresponds to the first-row, second-column (shear)
            component and the third element corresponds to the second-row, first-column
            (shear) component.
        dump_frequency
            By default, 1, meaning results are written out every increment.
        """

        _method_name = "planar_2D"
        _method_args = {
            "total_time": total_time,
            "num_increments": num_increments,
            "normal_direction": normal_direction,
            "target_def_grad": target_def_grad,
            "target_def_grad_rate": target_def_grad_rate,
            "dump_frequency": dump_frequency,
        }

        # Validation:
        if sum(t is not None for t in [target_def_grad_rate, target_def_grad]) != 1:
            raise ValueError(
                "Specify either `target_def_grad_rate` or `target_def_grad`."
            )
        if target_def_grad_rate is not None:
            def_grad_vals = target_def_grad_rate
        else:
            def_grad_vals = target_def_grad

        # Flatten list/array:
        if isinstance(def_grad_vals, list):
            if isinstance(def_grad_vals[0], list):
                def_grad_vals = [j for i in def_grad_vals for j in i]
        elif isinstance(def_grad_vals, np.ndarray):
            def_grad_vals = def_grad_vals.flatten()

        try:
            normal_dir_idx = cls._DIR_IDX.index(normal_direction)
        except ValueError:
            raise ValueError(
                f"Normal direction {normal_direction!r} not allowed. It should be one of "
                f'"x", "y" or "z".'
            )

        loading_col_idx = [0, 1, 2]
        loading_col_idx.remove(normal_dir_idx)
        dg_arr = np.ma.masked_array(np.zeros((3, 3)), mask=np.zeros((3, 3)))
        stress_arr = np.ma.masked_array(np.zeros((3, 3)), mask=np.zeros((3, 3)))

        dg_row_idx = [
            loading_col_idx[0],
            loading_col_idx[0],
            loading_col_idx[1],
            loading_col_idx[1],
        ]
        dg_col_idx = [
            loading_col_idx[0],
            loading_col_idx[1],
            loading_col_idx[0],
            loading_col_idx[1],
        ]
        dg_arr[dg_row_idx, dg_col_idx] = def_grad_vals
        dg_arr.mask[:, normal_dir_idx] = True
        stress_arr.mask[:, loading_col_idx] = True

        def_grad = dg_arr if target_def_grad is not None else None
        def_grad_rate = dg_arr if target_def_grad_rate is not None else None

        obj = cls(
            normal_direction=normal_direction,
            total_time=total_time,
            num_increments=num_increments,
            target_def_grad=def_grad,
            target_def_grad_rate=def_grad_rate,
            stress=stress_arr,
            dump_frequency=dump_frequency,
        )
        return obj._remember_name_args(_method_name, _method_args)

    @classmethod
    def random_2D(
        cls,
        total_time: int | float,
        num_increments: int,
        normal_direction: str,
        target_def_grad_rate: float | None = None,
        target_def_grad: float | None = None,
        dump_frequency: int = 1,
    ) -> Self:
        """
        Generate a random 2D planar load case.

        Parameters
        ----------
        total_time
            Total simulation time.
        num_increments
            Number of simulation increments.
        normal_direction
            A single character, "x", "y" or "z", representing the loading plane normal
            direction.
        target_def_grad_rate
            Maximum target deformation gradient rate component. Components will be sampled
            randomly in the interval [-target_def_grad_rate, +target_def_grad_rate).
        target_def_grad
            Maximum target deformation gradient component. Components will be sampled
            randomly in the interval [-target_def_grad, +target_def_grad).
        dump_frequency
            By default, 1, meaning results are written out every increment.
        """
        # TODO: shouldn't this be implemented in the same was as in random_3D?

        def_grad_vals = (np.random.random(4) - 0.5) * 2
        if target_def_grad_rate is not None:
            target_def_grad_rate *= def_grad_vals
        else:
            target_def_grad *= def_grad_vals
            target_def_grad += np.eye(2).reshape(-1)

        return cls.planar_2D(
            total_time=total_time,
            num_increments=num_increments,
            normal_direction=normal_direction,
            target_def_grad=target_def_grad,
            target_def_grad_rate=target_def_grad_rate,
            dump_frequency=dump_frequency,
        )

    @classmethod
    def random_3D(
        cls,
        total_time: int | float,
        num_increments: int,
        target_def_grad: float,
        dump_frequency: int = 1,
    ) -> Self:
        """
        Generate a random 3D case.

        Parameters
        ----------
        total_time
            Total simulation time.
        num_increments
            Number of simulation increments.
        target_def_grad
            Maximum target deformation gradient component. Components will be sampled
            randomly in the interval [-target_def_grad, +target_def_grad).
        dump_frequency
            By default, 1, meaning results are written out every increment.
        """
        _method_name = "random_3D"
        _method_args = {
            "total_time": total_time,
            "num_increments": num_increments,
            "target_def_grad": target_def_grad,
            "dump_frequency": dump_frequency,
        }

        # Five stretch components, since it's a symmetric matrix and the trace must be
        # zero:
        stretch_comps = (np.random.random((5,)) - 0.5) * target_def_grad
        stretch = np.zeros((3, 3)) * np.nan

        # Diagonal comps:
        stretch[[0, 1], [0, 1]] = stretch_comps[:2]
        stretch[2, 2] = -(stretch[0, 0] + stretch[1, 1])

        # Off-diagonal comps:
        stretch[[1, 0], [0, 1]] = stretch_comps[2]
        stretch[[2, 0], [0, 2]] = stretch_comps[3]
        stretch[[1, 2], [2, 1]] = stretch_comps[4]

        # Add the identity:
        U = stretch + np.eye(3)

        defgrad = U

        # Ensure defgrad has a unit determinant:
        defgrad = defgrad / (np.linalg.det(defgrad) ** (1 / 3))

        dg_arr = np.ma.masked_array(defgrad, mask=np.zeros((3, 3), dtype=int))
        stress_arr = np.ma.masked_array(
            np.zeros((3, 3), dtype=int), mask=np.ones((3, 3), dtype=int)
        )

        obj = cls(
            total_time=total_time,
            num_increments=num_increments,
            target_def_grad=dg_arr,
            stress=stress_arr,
            dump_frequency=dump_frequency,
        )
        return obj._remember_name_args(_method_name, _method_args)

    @classmethod
    def random_inc(
        cls,
        total_time: Union[int, float],
        num_increments: int,
        target_def_grad: float,
        start_def_grad: Optional[np.typing.ArrayLike] = None,
        dump_frequency: Optional[int] = 1,
    ) -> LoadStep:
        """Random load step continuing from a start point.

        Parameters
        ----------
        total_time : float or int
            Total simulation time.
        num_increments
            Number of simulation increments.
        target_def_grad : float
            Maximum of each deformation gradient component
        start_def_grad : numpy.ndarray of shape (3, 3), optional
            Starting deformation gradient of load step. Identity if not given.
        dump_frequency : int, optional
            By default, 1, meaning results are written out every increment.
        """
        if start_def_grad is None:
            start_def_grad = np.eye(3)
        if start_def_grad.shape != (3, 3):
            msg = "start_def_grad must be an array of shape (3, 3)"
            raise ValueError(msg)

        dg_arr = np.copy(start_def_grad)
        dg_arr += target_def_grad * np.where(np.random.random((3, 3)) > 0.5, 1.0, -1.0)
        dg_arr /= np.cbrt(np.linalg.det(dg_arr))

        return cls(
            total_time=total_time,
            num_increments=num_increments,
            target_def_grad=dg_arr,
            dump_frequency=dump_frequency,
        )

    @classmethod
    def random_inc(
        cls,
        total_time: Union[int, float],
        num_increments: int,
        target_def_grad: float,
        start_def_grad: Optional[np.typing.ArrayLike] = None,
        dump_frequency: Optional[int] = 1,
    ) -> LoadStep:
        """Random load step continuing from a start point.

        Parameters
        ----------
        total_time : float or int
            Total simulation time.
        num_increments
            Number of simulation increments.
        target_def_grad : float
            Maximum of each deformation gradient component
        start_def_grad : numpy.ndarray of shape (3, 3), optional
            Starting deformation gradient of load step. Identity if not given.
        dump_frequency : int, optional
            By default, 1, meaning results are written out every increment.
        """
        if start_def_grad is None:
            start_def_grad = np.eye(3)
        if start_def_grad.shape != (3, 3):
            msg = "start_def_grad must be an array of shape (3, 3)"
            raise ValueError(msg)

        dg_arr = np.copy(start_def_grad)
        dg_arr += target_def_grad * np.where(np.random.random((3, 3)) > 0.5, 1.0, -1.0)
        dg_arr /= np.cbrt(np.linalg.det(dg_arr))

        return cls(
            total_time=total_time,
            num_increments=num_increments,
            target_def_grad=dg_arr,
            dump_frequency=dump_frequency,
        )

    @classmethod
    def uniaxial_cyclic(
        cls,
        max_stress: float,
        min_stress: float,
        cycle_frequency: float,
        num_increments_per_cycle: int,
        num_cycles: int,
        direction: str,
        waveform: str = "sine",
        dump_frequency: int = 1,
    ) -> list[Self]:
        """
        Generate a cyclic stress case.

        Parameters
        ----------
        max_stress
            Maximum scalar stress.
        min_stress
            Minimum scalar stress.
        num_increments_per_cycle
            Number of simulation increments per cycle.
        num_cycles
            Total number of cycles.
        direction
            Direction in which to apply loading
        waveform
            Waveform of stress cycle.
            Only `sine` currently supported.
        dump_frequency
            By default, 1, meaning results are written out every increment.
        """
        try:
            loading_dir_idx = cls._DIR_IDX.index(direction)
        except ValueError:
            raise ValueError(
                f'Loading direction "{direction}" not allowed. It should be one of "x", '
                f'"y" or "z".'
            )

        cycle_time = 1 / cycle_frequency

        if waveform.lower() != "sine":
            raise NotImplementedError('Only waveform "sine" is currently allowed.')

        sig_mean = (max_stress + min_stress) / 2
        sig_diff = max_stress - min_stress

        A = 2 * np.pi / cycle_time
        time = np.linspace(0, 2 * np.pi, num=num_increments_per_cycle, endpoint=True) / A
        sig = (sig_diff / 2) * np.sin(A * time) + sig_mean

        time_per_inc = cycle_time / num_increments_per_cycle

        stress_mask = np.ones((sig.size, 3, 3))
        stress_mask[:, [0, 1, 2], [0, 1, 2]] = 0
        stress_arr = np.ma.masked_array(
            data=np.zeros((sig.size, 3, 3)),
            mask=stress_mask,
        )
        stress_arr[:, loading_dir_idx, loading_dir_idx] = sig

        dg_arr = np.ma.masked_array(np.zeros((3, 3)), mask=np.eye(3))

        cycle: list[dict[str, Any]] = []
        for time_idx, _ in enumerate(time):
            cycle.append(
                {
                    "num_increments": 1,
                    "total_time": time_per_inc,
                    "stress": stress_arr[time_idx],
                    "target_def_grad": dg_arr,
                    "dump_frequency": dump_frequency,
                }
            )

        out: list[dict[str, Any]] = []
        for cycle_idx in range(num_cycles):
            cycle_i = copy.deepcopy(cycle)
            if cycle_idx != num_cycles - 1:
                # intermediate cycle; remove repeated increment:
                cycle_i = cycle_i[:-1]
            out.extend(cycle_i)
        return [cls(**i)._remember_name_args(None, i) for i in out]

    @classmethod
    def from_npz_file(
        cls,
        npz_file_path: str,
        idx: int,
    ) -> list[Self]:
        """
        Construct a list of load steps using data from a Numpy .npz file. This is designed for running large arrays of simulations from the data in this file, where each uses a loadcase specified by a given index (`idx`).

        Parameters
        ----------
        npz_file_path: str
            Filepath to the npz file, which must be dict-like with at least the following keys:
            num_incs: 1D numpy array
                Array of the total number of increments to use for each loadcase.
                (total number of increments the damask simulation should undergo)
            inc_size: 2D numpy array
                Array of the amount of strain each loadstep of each loadcase should undergo in the damask simulation.
                (1st D is loadstep, 2nd is principle components of strain.)
            inc_size_final: 2D numpy array
                Array of amount of strain of final loadsteps.
                (1st D is loadstep, 2nd is principle components of strain.)
            u_sampled_split: 4D numpy array
                Array of strain matrices (loadcase 1st D, loadstep 2nd D, strain matrix 3rd, 4th Ds). Sampled from the elements of an FE model.
            strain_rate: 1D numpy array of one float
                Scalar strain rate to be used for every simulation
        idx: int
            int index of desired loadcase to use.
        """

        data = np.load(npz_file_path)
        num_incs = data["num_incs"]
        inc_size = data["inc_size"]
        inc_size_final = data["inc_size_final"]
        u_sampled_split = data["u_sampled_split"]
        strain_rate = data["strain_rate"]

        load_steps = []
        for j in range(num_incs[idx]):
            inc_size_idx = (idx,) + (2,) * (len(inc_size.shape) - 1)
            if j == num_incs[idx] - 1:
                # final inc
                dt = inc_size_final[inc_size_idx]
            else:
                dt = inc_size[inc_size_idx]
            dt = abs(dt) / strain_rate

            load_steps.append(
                {
                    "target_def_grad": u_sampled_split[idx, j],
                    "total_time": dt.item(),
                    "num_increments": 1,
                }
            )

        return [cls(**i)._remember_name_args(None, i) for i in load_steps]


@dataclass
class LoadCase(ParameterValue):
    """
    A loading case, consisting of a sequence of loadings to apply.
    """

    # TODO: store step data (e.g. stress tensor for each step) in combined arrays; steps
    # can be a (cached) property that indexes those arrays?

    _typ: ClassVar[str] = "load_case"

    #: The steps in the loading case.
    steps: list[LoadStep]

    def __post_init__(self):
        for step_idx in range(len(self.steps)):
            step = self.steps[step_idx]
            if not isinstance(step, LoadStep):
                step_i = copy.deepcopy(cast(dict, step))  # don't mutate
                _method_name = step_i.pop("_method_name", None)
                _method_args = step_i.pop("_method_args", None)
                self.steps[step_idx] = LoadStep(**step_i)
                self.steps[step_idx]._method_name = _method_name
                self.steps[step_idx]._method_args = _method_args

    def __len__(self) -> int:
        return len(self.steps)

    def __iter__(self) -> Iterator[LoadStep]:
        yield from self.steps

    @property
    def num_steps(self) -> int:
        """
        The number of steps in the case.
        """
        return len(self.steps)

    @property
    def type(self) -> str | list[str]:
        """
        The type of the step if there is only a single step,
        or the types if there are multiple steps.
        """
        if self.num_steps == 1:
            return self.steps[0].type
        else:
            return self.types

    @property
    def types(self) -> list[str]:
        """
        The types of the steps.
        """
        return [i.type for i in self.steps]

    def create_damask_loading_plan(self) -> list[dict[str, Any]]:
        """
        Turn this load case into a DAMASK loading plan.
        """
        load_steps: list[dict[str, Any]] = []
        for step in self.steps:
            dct = step.to_dict()
            dct["def_grad_aim"] = dct.pop("target_def_grad", None)
            dct["def_grad_rate"] = dct.pop("target_def_grad_rate", None)
            load_steps.append(dct)
        return load_steps

    @classmethod
    def uniaxial(cls, **kwargs) -> Self:
        """A single-step uniaxial load case.

        See :py:meth:`~LoadStep.uniaxial` for argument documentation.

        """
        return cls(steps=[LoadStep.uniaxial(**kwargs)])

    @classmethod
    def biaxial(cls, **kwargs) -> Self:
        """A single-step biaxial load case.

        See :py:meth:`~`LoadStep.biaxial` for argument documentation.

        """
        return cls(steps=[LoadStep.biaxial(**kwargs)])

    @classmethod
    def plane_strain(cls, **kwargs) -> Self:
        """A single-step plane-strain load case.

        See :py:meth:`~LoadStep.plane_strain` for argument documentation.

        """
        return cls(steps=[LoadStep.plane_strain(**kwargs)])

    @classmethod
    def planar_2D(cls, **kwargs) -> Self:
        """A single-step planar 2D load case.

        See :py:meth:`~LoadStep.planar_2D` for argument documentation.

        """
        return cls(steps=[LoadStep.planar_2D(**kwargs)])

    @classmethod
    def random_2D(cls, **kwargs) -> Self:
        """A single-step random 2D load case.

        See :py:meth:`~LoadStep.random_2D` for argument documentation.

        """
        return cls(steps=[LoadStep.random_2D(**kwargs)])

    @classmethod
    def random_3D(cls, **kwargs) -> Self:
        """A single-step random 3D load case.

        See :py:meth:`~LoadStep.random_3D` for argument documentation.
        """
        return cls(steps=[LoadStep.random_3D(**kwargs)])

    @classmethod
    def uniaxial_cyclic(cls, **kwargs) -> Self:
        """Uniaxial cyclic loading.

        See :py:meth:`~LoadStep.uniaxial_cyclic` for argument documentation.
        """
        return cls(steps=LoadStep.uniaxial_cyclic(**kwargs))

    @classmethod
    def example_uniaxial(cls) -> Self:
        """A non-parametrisable example single-step uniaxial load case."""
        return cls(steps=[LoadStep.example_uniaxial()])

    @classmethod
    def multistep(cls, steps: list[dict[str, Any] | LoadStep]) -> Self:
        """A load case with multiple steps.

        Parameters
        ----------
        steps
            A list of `LoadStep` objects or `dict`s representing `LoadStep` objects, in
            which case if a `dict` has a key `type`, the corresponding `LoadStep`
            classmethod will be invoked with the remainder of the `dict` items.
        """
        step_objs: list[LoadStep] = []
        for step_i in steps:
            if isinstance(step_i, LoadStep):
                step_objs.append(step_i)
            else:
                # assume a dict
                step_dict = copy.deepcopy(step_i)  # don't mutate
                if (step_i_type := step_dict.pop("type", None)) and (
                    step_i_type != LoadStep.__name__
                ):
                    # assume a LoadStep class method:
                    try:
                        method: Callable[..., LoadStep | list[LoadStep]] = getattr(
                            LoadStep, step_i_type
                        )
                    except AttributeError:
                        raise ValueError(
                            f"No `LoadStep` method named {step_i_type!r} for load step "
                            f"specification {step_dict!r}."
                        )
                    steps = method(**step_dict)
                    if isinstance(steps, LoadStep):
                        step_objs.append(steps)
                    else:
                        # in the general case, multiple `LoadStep`s might be generated:
                        step_objs.extend(steps)
                else:
                    step_objs.append(LoadStep(**step_dict))

        return cls(steps=step_objs)

    @classmethod
    def from_npz_file(cls, **kwargs) -> Self:
        """Importing loadcase from npz file

        See :py:meth:`~LoadStep.from_npz_file` for argument documentation.
        """
        return cls(steps=LoadStep.from_npz_file(**kwargs))

    @classmethod
    def multistep_random_inc(
        cls,
        steps: List[Dict],
        interpolate_steps: int,
        interpolate_kind: Optional[Union[str, int]] = 3,
    ) -> LoadCase:
        """A load case with multiple steps.

        Parameters
        ----------

        """
        from scipy.interpolate import interp1d

        step_objs = []
        dg_arr = [np.eye(3)]
        for step_i in steps:
            step_i = copy.deepcopy(step_i)  # don't mutate
            repeats = step_i.pop("repeats", 1)
            method = LoadStep.random_inc
            for _ in range(repeats):
                step_obj = method(**step_i, start_def_grad=dg_arr[-1])
                dg_arr.append(step_obj.target_def_grad)
                step_objs.append(step_obj)
        dg_arr = np.array(dg_arr)

        dg_interp = interp1d(
            np.arange(len(dg_arr)) * interpolate_steps,
            dg_arr,
            kind=interpolate_kind,
            axis=0,
        )

        step_objs_full = []
        for i, step_obj_i in enumerate(step_objs):
            step_i = {
                "total_time": step_obj_i.total_time / interpolate_steps,
                "num_increments": int(step_obj_i.num_increments / interpolate_steps),
                "dump_frequency": step_obj_i.dump_frequency,
            }
            for j in range(interpolate_steps):
                dg = dg_interp(i * interpolate_steps + j + 1)
                step_objs_full.append(LoadStep(**step_i, target_def_grad=dg))

        return cls(steps=step_objs_full)
