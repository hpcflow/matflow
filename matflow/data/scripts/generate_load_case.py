from __future__ import annotations

from matflow.param_classes.load import LoadCase


def generate_load_case(
    total_time: float | int,
    num_increments: int,
    direction: str,
    target_def_grad_rate: float,
) -> dict[str, LoadCase]:
    """Generate a single-step uniaxial load case."""
    return {
        "load_case": LoadCase.uniaxial(
            total_time=total_time,
            num_increments=num_increments,
            direction=direction,
            target_def_grad_rate=target_def_grad_rate,
        )
    }
