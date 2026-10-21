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


def _values_equal(left: Any, right: Any) -> bool:
    """Compare nested result data, including NumPy arrays and NaNs."""

    if isinstance(left, np.ndarray) or isinstance(right, np.ndarray):
        if not (isinstance(left, np.ndarray) and isinstance(right, np.ndarray)):
            return False

        return np.array_equal(
            left,
            right,
            equal_nan=True,
        )

    if is_dataclass(left) or is_dataclass(right):
        if not (is_dataclass(left) and is_dataclass(right) and type(left) is type(right)):
            return False

        return all(
            _values_equal(
                getattr(left, field.name),
                getattr(right, field.name),
            )
            for field in fields(left)
        )

    if isinstance(left, dict) or isinstance(right, dict):
        if not (
            isinstance(left, dict)
            and isinstance(right, dict)
            and left.keys() == right.keys()
        ):
            return False

        return all(_values_equal(left[key], right[key]) for key in left)

    if isinstance(left, (list, tuple)) or isinstance(right, (list, tuple)):
        if type(left) is not type(right) or len(left) != len(right):
            return False

        return all(_values_equal(a, b) for a, b in zip(left, right))

    # Treat NaN diagnostics as equal.
    if (
        isinstance(left, (float, np.floating))
        and isinstance(right, (float, np.floating))
        and np.isnan(left)
        and np.isnan(right)
    ):
        return True

    return bool(left == right)
