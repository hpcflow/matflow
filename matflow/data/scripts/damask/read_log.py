from __future__ import annotations
from pathlib import Path
from damask_parse.readers import read_spectral_stdout


def read_log(damask_stdout_file: str | Path) -> dict:
    try:
        return read_spectral_stdout(path=damask_stdout_file, encoding="utf8")
    except UnicodeDecodeError:
        # Docker on Windows...
        return read_spectral_stdout(path=damask_stdout_file, encoding="utf16")
