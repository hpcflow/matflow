"""Utility functions to assist testing."""

from dataclasses import fields, is_dataclass
from functools import partial
from typing import Any

from hpcflow.sdk.core.test_utils import (
    make_test_data_YAML_workflow,
    make_test_data_YAML_workflow_template,
)
import numpy as np

import matflow as mf

make_test_data_YAML_workflow = partial(
    make_test_data_YAML_workflow, app=mf, pkg="matflow.tests.data"
)

make_test_data_YAML_workflow_template = partial(
    make_test_data_YAML_workflow_template, app=mf, pkg="matflow.tests.data"
)


def assert_values_equal(
    actual: Any,
    expected: Any,
    *,
    rtol: float = 1e-7,
    atol: float = 0.0,
    equal_nan: bool = True,
) -> None:
    """Assert that two nested values are equal.

    This is a test helper that compares nested dict/list structures and handles
    NumPy arrays (and array-like lists) in a sensible way.

    - Numeric arrays use `assert_allclose` (configurable tolerances).
    - Non-numeric arrays use `assert_array_equal`.
    - `NaN` scalar values are treated as equal.

    Parameters
    ----------
    actual, expected
        Values to compare.
    rtol, atol
        Tolerances used for numeric arrays.
    equal_nan
        Whether NaNs compare equal for numeric arrays.
    """

    def fmt_path(path_parts: list[str]) -> str:
        return "".join(path_parts) if path_parts else "<root>"

    def is_number_array(arr: np.ndarray) -> bool:
        return arr.dtype.kind in {"f", "c", "i", "u", "b"}

    def coerce_array(value: Any) -> np.ndarray:
        if isinstance(value, np.ndarray):
            return value
        if isinstance(value, (list, tuple)):
            return np.asarray(value)
        if isinstance(value, np.generic):
            return np.asarray(value)
        raise TypeError(f"Cannot coerce type {type(value)!r} to ndarray")

    def rec(a: Any, b: Any, path: list[str]) -> None:
        # Handle array-vs-arraylike first.
        if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
            arr_a = coerce_array(a)
            arr_b = coerce_array(b)
            if is_number_array(arr_a) and is_number_array(arr_b):
                np.testing.assert_allclose(
                    arr_a,
                    arr_b,
                    rtol=rtol,
                    atol=atol,
                    equal_nan=equal_nan,
                    err_msg=f"Mismatch at {fmt_path(path)}",
                )
            else:
                np.testing.assert_array_equal(
                    arr_a,
                    arr_b,
                    err_msg=f"Mismatch at {fmt_path(path)}",
                )
            return

        # Dataclasses (e.g. ParameterValue objects)
        if is_dataclass(a) or is_dataclass(b):
            assert (
                is_dataclass(a) and is_dataclass(b) and type(a) is type(b)
            ), f"Mismatch at {fmt_path(path)}: {type(a)!r} != {type(b)!r}"
            for field in fields(a):
                rec(
                    getattr(a, field.name),
                    getattr(b, field.name),
                    path + [f".{field.name}"],
                )
            return

        # Dicts
        if isinstance(a, dict) or isinstance(b, dict):
            assert isinstance(a, dict) and isinstance(
                b, dict
            ), f"Mismatch at {fmt_path(path)}: {type(a)!r} != {type(b)!r}"
            assert (
                a.keys() == b.keys()
            ), f"Mismatch at {fmt_path(path)}: keys differ: {a.keys()!r} != {b.keys()!r}"
            for key in a.keys():
                rec(a[key], b[key], path + [f"[{key!r}]"])
            return

        # Sequences
        if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
            assert type(a) is type(
                b
            ), f"Mismatch at {fmt_path(path)}: {type(a)!r} != {type(b)!r}"
            assert len(a) == len(
                b
            ), f"Mismatch at {fmt_path(path)}: len {len(a)} != {len(b)}"
            for idx, (ai, bi) in enumerate(zip(a, b)):
                rec(ai, bi, path + [f"[{idx}]"])
            return

        # Treat NaN diagnostics as equal.
        if (
            isinstance(a, (float, np.floating))
            and isinstance(b, (float, np.floating))
            and np.isnan(a)
            and np.isnan(b)
        ):
            return

        assert a == b, f"Mismatch at {fmt_path(path)}: {a!r} != {b!r}"

    rec(actual, expected, [])


def values_equal(
    left: Any,
    right: Any,
    *,
    rtol: float = 1e-7,
    atol: float = 0.0,
    equal_nan: bool = True,
) -> bool:
    """Bool wrapper around :func:`assert_values_equal`."""
    try:
        assert_values_equal(left, right, rtol=rtol, atol=atol, equal_nan=equal_nan)
    except AssertionError:
        return False
    return True
