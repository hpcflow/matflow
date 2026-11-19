from pathlib import Path

import numpy as np


PHASE_FIELD_SHAPE = (50, 62_500)


def load_fifty_grain_phase_fields(phase_field_data: str | Path) -> np.ndarray:
    with np.load(Path(phase_field_data), allow_pickle=False) as archive:
        phase_fields = archive["phase_fields"]

    if phase_fields.shape != PHASE_FIELD_SHAPE:
        raise ValueError(
            "The Fifty Grain phase-field data must have shape "
            f"{PHASE_FIELD_SHAPE}, got {phase_fields.shape}."
        )
    if not np.all(np.isfinite(phase_fields)):
        raise ValueError("The Fifty Grain phase-field data must be finite.")

    return phase_fields
