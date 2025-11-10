"""
Miscellaneous utility functions.
"""
from __future__ import annotations
from typing_extensions import TypeIs
import numpy as np
from numpy.typing import NDArray
from pathlib import Path


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


def read_numeric_csv_file(
    path: str,
    number: int | None = None,
    start_index: int = 0,
    delimiter: str = " ",
    columns: list[int] | None = None,
    exc_msg: str | None = None,
) -> NDArray:
    """
    Load data from a text file.

    Parameters
    ----------
    path
        Path to the file to load from.
    number
        Number of lines to read from the file.
    start_index
        The line number of the file that the seeds start at.
        Allows skipping headers.
    delimiter
        The delimiter separating values in the file.
        Defaults to space, but commas and tabs are also sensible
        (and correspond to CSV and TSV files respectively).
    columns
        The columns in the file to read from.
        Defaults to reading every column.
    exc_msg:
        ValueError message to return.
    """
    data: list[list[float]] = []
    with Path(path).open("rt") as fh:
        for idx, line in enumerate(fh):
            line = line.strip()
            if not line or idx < start_index:
                continue
            elif len(data) < number if number is not None else True:
                values = line.split(delimiter)
                if idx == start_index:
                    columns = columns or list(range(len(values)))
                data.append([float(values[i]) for i in columns])
    if number is not None and len(data) < number:
        exc_msg = exc_msg or "Not enough lines in the file."
        raise ValueError(exc_msg)

    return np.asarray(data)
