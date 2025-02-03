"""
Miscellaneous utility functions.
"""
from __future__ import annotations
from typing_extensions import TypeIs
import numpy as np
from numpy.typing import NDArray


def _is_list_of_lists(arr: list[float] | list[list[float]]) -> TypeIs[list[list[float]]]:
    return isinstance(arr[0], list)


def masked_array_from_list(
    arr: list[float] | list[list[float]], fill_value: str = "x"
) -> NDArray:
    """Generate a (masked) array from a 1D or 2D list whose elements may contain a fill
    value."""

    is_2D = False
    if _is_list_of_lists(arr):
        is_2D = True
        n_rows = len(arr)
        arr = [item for row in arr for item in row]

    data = np.empty(len(arr))
    mask = np.full(len(arr), False)
    has_mask = False
    for idx, i in enumerate(arr):
        if i == fill_value:
            mask[idx] = True
            has_mask = True
        else:
            data[idx] = i
    if has_mask:
        out = np.ma.masked_array(data, mask=mask)
    else:
        out = data
    if is_2D:
        out = out.reshape(n_rows, -1, order="C")
    return out
