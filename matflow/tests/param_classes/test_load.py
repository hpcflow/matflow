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


def test_load_case_yaml_init(tmp_path: Path, load_case_1: LoadCase):
    wk = make_test_data_YAML_workflow("define_load.yaml", path=tmp_path)
    load_case = wk.tasks.define_load_case_1.elements[0].inputs.load_case.value
    assert load_case == load_case_1

    # second task uses the `load_case::random_polynomial` syntax with a fixed seed:
    load_case_poly = wk.tasks.define_load_case_2.elements[0].inputs.load_case.value
    assert load_case_poly == LoadCase.random_polynomial(
        total_time=100,
        num_steps=10,
        coefficient_ranges=[[-1e-3, 1e-3], [-1e-5, 1e-5], [-1e-7, 1e-7]],
        num_increments=20,
        seed=12345,
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


def test_load_case_random_polynomial():
    args = {
        "total_time": 10.0,
        "num_steps": 5,
        "coefficient_ranges": [[-0.01, 0.01], [-0.001, 0.001], [-0.0001, 0.0001]],
        "num_increments": 4,
        "dump_frequency": 2,
        "seed": 123,
    }
    lc = LoadCase.random_polynomial(**args)
    assert lc.num_steps == args["num_steps"]
    for step in lc.steps:
        assert step.total_time == args["total_time"] / args["num_steps"]
        assert step.num_increments == args["num_increments"]
        assert step.dump_frequency == args["dump_frequency"]
        assert step.target_def_grad.shape == (3, 3)
        assert not np.any(step.target_def_grad.mask)
        assert np.all(step.stress.mask)
        assert np.isclose(np.linalg.det(step.target_def_grad.data), 1.0)

    # reproducible with the same seed, different otherwise:
    assert lc == LoadCase.random_polynomial(**args)
    assert lc != LoadCase.random_polynomial(**{**args, "seed": 124})

    # same result via `multistep`:
    assert lc == LoadCase.multistep(steps=[{"type": "random_polynomial", **args}])


def test_load_case_random_polynomial_evaluates_polynomial():
    # with degenerate ranges the coefficients are known exactly:
    c_1, c_2, c_3 = 0.01, -0.001, 0.0002
    num_steps = 4
    total_time = 2.0
    lc = LoadCase.random_polynomial(
        total_time=total_time,
        num_steps=num_steps,
        coefficient_ranges=[[c_1, c_1], [c_2, c_2], [c_3, c_3]],
    )
    dt = total_time / num_steps
    for step_idx, step in enumerate(lc.steps):
        t = (step_idx + 1) * dt
        expected = np.eye(3) + c_1 * t + c_2 * t**2 + c_3 * t**3
        expected /= np.cbrt(np.linalg.det(expected))
        assert np.allclose(step.target_def_grad.data, expected)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"coefficient_ranges": [0.1, 0.2]},
        {"coefficient_ranges": []},
        {"coefficient_ranges": [[0.2, 0.1]]},
        {"num_steps": 0},
        # large linear coefficient leads to a non-positive determinant:
        {"coefficient_ranges": [[-5.0, -5.0]]},
    ],
)
def test_load_case_random_polynomial_raises(kwargs):
    args = {
        "total_time": 1.0,
        "num_steps": 2,
        "coefficient_ranges": [[-0.01, 0.01]],
        **kwargs,
    }
    with pytest.raises(ValueError):
        LoadCase.random_polynomial(**args)
