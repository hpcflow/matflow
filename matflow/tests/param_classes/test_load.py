import sys
from pathlib import Path

import pytest
import requests
import numpy as np

import matflow as mf
from matflow.param_classes import LoadCase
from matflow.tests.utils import make_test_data_YAML_workflow


def test_single_multistep_uniaxial():
    args = {
        "num_increments": 200,
        "total_time": 100,
        "direction": "x",
        "target_def_grad_rate": 1e-3,
    }
    lc1 = LoadCase.uniaxial(**args)
    lc2 = LoadCase.multistep(steps=[{"type": "uniaxial", **args}])
    assert lc1 == lc2


def test_load_case_yaml_init(null_config, tmp_path: Path, load_case_1: LoadCase):
    wk = make_test_data_YAML_workflow("define_load.yaml", path=tmp_path)
    load_case = wk.tasks.define_load_case.elements[0].inputs.load_case.value
    assert load_case == load_case_1


@pytest.mark.xfail(
    condition=sys.platform == "darwin",
    raises=requests.exceptions.HTTPError,
    reason=(
        "GHA MacOS runners use the same IP address, so we get rate limited when "
        "retrieving demo data from GitHub."
    ),
)
def test_load_case_from_npz_file():
    npz_file_path = mf.get_demo_data_file_path("load_cases.npz")
    file_dat = np.load(npz_file_path)
    for lc_idx in (0, 1, 2):
        lc = mf.LoadCase.from_npz_file(npz_file_path=npz_file_path, idx=lc_idx)
        all_times = []
        all_num_incs = []
        all_dirs = []
        all_normal_dirs = []
        all_target_def_grads = []
        all_target_def_grad_rates = []
        all_stresses = []
        all_dump_freqs = []
        for ls in lc.steps:
            all_times.append(ls.total_time)
            all_num_incs.append(ls.num_increments)
            all_dirs.append(ls.direction)
            all_normal_dirs.append(ls.normal_direction)
            all_target_def_grads.append(ls.target_def_grad)
            all_target_def_grad_rates.append(ls.target_def_grad_rate)
            all_stresses.append(ls.stress)
            all_dump_freqs.append(ls.dump_frequency)

        assert len(lc.steps) == file_dat["num_incs"][lc_idx]
        assert set(all_stresses) == {None}
        assert set(all_stresses) == {None}
        assert set(all_times) == {
            float(abs(file_dat["inc_size"][lc_idx][2]) / file_dat["strain_rate"]),
            float(abs(file_dat["inc_size_final"][lc_idx][2]) / file_dat["strain_rate"]),
        }
        assert set(all_num_incs) == {1}
        assert set(all_dirs) == {None}
        assert set(all_normal_dirs) == {None}
        assert np.allclose(
            np.array(all_target_def_grads), file_dat["u_sampled_split"][lc_idx]
        )
        assert set(all_target_def_grad_rates) == {None}
        assert set(all_stresses) == {None}
        assert set(all_dump_freqs) == {1}
