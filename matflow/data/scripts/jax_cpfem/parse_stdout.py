import os
import re
from pathlib import Path

import numpy as np

_PAT_FP = (
    r"Fp\s*=\s*\[\[\s*([-+]?\d*\.\d*\s+[-+]?\d*\.\d*\s+[-+]?\d*\.\d*)\s*\]\s*"
    r"\[\s*([-+]?\d*\.\d*\s+[-+]?\d*\.\d*\s+[-+]?\d*\.\d*)\s*\]\s*"
    r"\[\s*([-+]?\d*\.\d*\s+[-+]?\d*\.\d*\s+[-+]?\d*\.\d*)\s*\]\s*\]"
)
_PAT_key_data_list = R"{key}:\s*\[\s*((?:\d+\.\d+\s*)+)\]"
_PAT_STRESS_XX = _PAT_key_data_list.format(key="stress_xx")
_PAT_STRESS_YY = _PAT_key_data_list.format(key="stress_yy")
_PAT_STRESS_ZZ = _PAT_key_data_list.format(key="stress_zz")
_PAT_STRESS_VM = _PAT_key_data_list.format(key="von_mises_stress")


def parse_stdout(jax_cpfem_stdout: Path):

    encoding = "utf-16" if os.name == "nt" else "utf-8"  # docker on windows nonsense
    with jax_cpfem_stdout.open("rt", encoding=encoding) as fh:
        contents = fh.read()

    fp = []
    for fp_res in re.findall(_PAT_FP, contents):
        fp.append([[float(i) for i in fp_row.split()] for fp_row in fp_res])
    fp_arr = np.asarray(fp)

    stress_xx = np.array(
        [float(i) for i in re.search(_PAT_STRESS_XX, contents).groups()[0].split()]
    )
    stress_yy = np.array(
        [float(i) for i in re.search(_PAT_STRESS_YY, contents).groups()[0].split()]
    )
    stress_zz = np.array(
        [float(i) for i in re.search(_PAT_STRESS_ZZ, contents).groups()[0].split()]
    )
    stress_von_mises = np.array(
        [float(i) for i in re.search(_PAT_STRESS_VM, contents).groups()[0].split()]
    )

    return {
        "Fp": fp_arr,
        "stress_xx": stress_xx,
        "stress_yy": stress_yy,
        "stress_zz": stress_zz,
        "stress_von_mises": stress_von_mises,
    }
