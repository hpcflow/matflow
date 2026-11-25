from __future__ import annotations

from matflow.data.scripts.generate_load_case import generate_load_case
from matflow.param_classes.load import LoadCase


def generate_load_cases(
    num_load_cases: int,
    total_time: float | int,
    num_increments: int,
    direction: str,
    target_def_grad_rate: float,
) -> dict[str, list[LoadCase]]:
    """Generate independent uniaxial load cases with the same loading parameters."""
    if (
        isinstance(num_load_cases, bool)
        or not isinstance(num_load_cases, int)
        or num_load_cases < 1
    ):
        raise ValueError("num_load_cases must be a positive integer.")
    return {
        "load_case": [
            generate_load_case(
                total_time=total_time + idx,
                num_increments=num_increments,
                direction=direction,
                target_def_grad_rate=target_def_grad_rate,
            )["load_case"]
            for idx in range(num_load_cases)
        ]
    }
