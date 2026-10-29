import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
import numpy as np

import matflow as mf
from matflow.param_classes import LoadCase
from matflow.data.scripts.generate_load_case import generate_load_case
from matflow.data.scripts.generate_load_cases import generate_load_cases
from matflow.data.scripts.generate_load_cases_random_exponential import (
    generate_load_cases_random_exponential,
)
from matflow.tests.utils import make_test_data_YAML_workflow


def test_generate_load_case():
    inputs = {
        "total_time": 100,
        "num_increments": 200,
        "direction": "x",
        "target_def_grad_rate": 1e-3,
    }
    result = generate_load_case(**inputs)

    assert isinstance(result["load_case"], LoadCase)
    assert result["load_case"] == LoadCase.uniaxial(**inputs)


@pytest.mark.parametrize("num_load_cases", [1, 3])
@pytest.mark.parametrize("direction", ["x", "y", "z"])
def test_generate_load_cases(num_load_cases: int, direction: str) -> None:
    result = generate_load_cases(
        num_load_cases=num_load_cases,
        total_time=10,
        num_increments=20,
        direction=direction,
        target_def_grad_rate=2e-3,
    )
    assert set(result) == {"load_case"}
    load_cases = result["load_case"]
    assert len(load_cases) == num_load_cases
    expected = lambda idx: LoadCase.uniaxial(
        total_time=10 + idx,
        num_increments=20,
        direction=direction,
        target_def_grad_rate=2e-3,
    )
    assert all(
        isinstance(case, LoadCase) and case == expected(idx)
        for idx, case in enumerate(load_cases)
    )
    assert len({id(case) for case in load_cases}) == num_load_cases
    assert len({id(case.steps[0]) for case in load_cases}) == num_load_cases


@pytest.mark.parametrize("num_load_cases", [0, -1, True])
def test_generate_load_cases_invalid_count(num_load_cases: int) -> None:
    with pytest.raises(ValueError, match="num_load_cases must be a positive integer"):
        generate_load_cases(
            num_load_cases=num_load_cases,
            total_time=100,
            num_increments=200,
            direction="x",
            target_def_grad_rate=1e-3,
        )


def test_generate_load_cases_schema() -> None:
    template = mf.WorkflowTemplate.from_YAML_string(
        "name: generate_load_cases_test\n"
        "tasks:\n"
        "  - schema: generate_load_cases_uniaxial\n"
        "    inputs:\n"
        "      num_load_cases: 3\n"
    )
    output = template.tasks[0].all_schema_outputs[0]
    assert output.parameter.typ == "load_case"
    assert output.multiplicity == "<<input:num_load_cases>>"
    assert output.resolve_multiplicity(3) == 3


@pytest.mark.parametrize("conserve_volume", [True, False])
def test_generate_load_cases_random_exponential(conserve_volume):
    args = {
        "num_load_cases": 3,
        "total_time": 100,
        "num_steps": 100,
        "num_increments": 4,
        "conserve_volume": conserve_volume,
        "seed": 123,
    }
    result = generate_load_cases_random_exponential(**args)
    assert set(result) == {"load_case", "monotonicity"}
    assert 0 < result["monotonicity"] <= 1
    if not conserve_volume:
        assert result["monotonicity"] == 1
    cases = result["load_case"]
    assert len(cases) == args["num_load_cases"]

    for case in cases:
        assert isinstance(case, LoadCase)
        assert len(case.steps) == args["num_steps"]
        gradients = np.array([np.eye(3)] + [s.target_def_grad.data for s in case.steps])
        differences = np.diff(gradients, axis=0)
        assert np.all(np.all(differences <= 0, axis=0) | np.all(differences >= 0, axis=0))
        if conserve_volume:
            np.testing.assert_allclose(np.linalg.det(gradients), 1)
        else:
            assert not np.allclose(np.linalg.det(gradients), 1)
        assert sum(step.total_time for step in case.steps) == args["total_time"]
        for step in case.steps:
            assert step.num_increments == args["num_increments"]
            assert step.total_time == args["total_time"] / args["num_steps"]
            assert not np.any(step.target_def_grad.mask)
            assert np.all(step.stress.mask)

    assert cases == generate_load_cases_random_exponential(**args)["load_case"]
    assert (
        cases
        != generate_load_cases_random_exponential(**{**args, "seed": 124})["load_case"]
    )


@pytest.mark.parametrize(
    "kwargs, parameter",
    [({"num_load_cases": value}, "num_load_cases") for value in [0, -1, True, 1.5]]
    + [({"num_steps": value}, "num_steps") for value in [0, -1, True, 1.5]]
    + [({"num_increments": value}, "num_increments") for value in [0, -1, True, 1.5]]
    + [({"max_tries": value}, "max_tries") for value in [0, -1, True, 1.5]]
    + [({"total_time": value}, "total_time") for value in [0, -1, np.inf, np.nan]],
)
def test_generate_load_cases_random_exponential_invalid_inputs(kwargs, parameter):
    args = {"num_load_cases": 1, "total_time": 100, "num_steps": 100}
    with pytest.raises(ValueError, match=parameter):
        generate_load_cases_random_exponential(**{**args, **kwargs})


def test_generate_load_cases_random_exponential_monotonicity(monkeypatch):
    rng = Mock(wraps=np.random.default_rng(123))
    monkeypatch.setattr(np.random, "default_rng", lambda seed: rng)
    result = generate_load_cases_random_exponential(
        num_load_cases=3, total_time=100, num_steps=100, seed=123
    )
    # Each attempted path samples k and deltaF, including rejected paths.
    attempts = rng.uniform.call_count // 2
    assert attempts > 3
    assert result["monotonicity"] == 3 / attempts


@pytest.mark.parametrize("parameter", ["k_range", "delta_f_range"])
@pytest.mark.parametrize("bounds", [[], [0], [[0, 1]], [1, 0], [0, np.inf], [np.nan, 1]])
def test_generate_load_cases_random_exponential_invalid_range(parameter, bounds):
    with pytest.raises(ValueError, match=parameter):
        generate_load_cases_random_exponential(
            num_load_cases=1, total_time=100, num_steps=10, **{parameter: bounds}
        )


def test_generate_load_cases_random_exponential_sampling_ranges():
    args = {"num_load_cases": 1, "total_time": 100, "num_steps": 10, "seed": 123}
    with pytest.raises(ValueError, match="k_range"):
        generate_load_cases_random_exponential(**args, k_range=(-0.1, 0.1))
    # Zero decay or zero amplitude must produce an undeformed path.
    for ranges in (
        {"k_range": [0, 0], "delta_f_range": [0.2, 0.3]},
        {"k_range": [0.02, 0.03], "delta_f_range": [0, 0]},
    ):
        result = generate_load_cases_random_exponential(**args, **ranges)
        assert result["monotonicity"] == 1
        for step in result["load_case"][0].steps:
            np.testing.assert_array_equal(step.target_def_grad.data, np.eye(3))


def test_generate_load_cases_random_exponential_invalid_determinants():
    # Large negative amplitudes make these candidates physically invalid.
    with pytest.raises(RuntimeError, match="within 2 attempts"):
        generate_load_cases_random_exponential(
            num_load_cases=1,
            total_time=100,
            num_steps=10,
            k_range=[0.1, 0.1],
            delta_f_range=[-2, -2],
            max_tries=2,
        )


def test_generate_load_cases_random_exponential_max_tries():
    # With volume conservation disabled, every candidate is monotonic.
    args = {
        "num_load_cases": 3,
        "total_time": 100,
        "num_steps": 10,
        "conserve_volume": False,
        "seed": 123,
    }
    with pytest.raises(RuntimeError, match="within 2 attempts"):
        generate_load_cases_random_exponential(**args, max_tries=2)
    cases = generate_load_cases_random_exponential(**args, max_tries=3)["load_case"]
    assert len(cases) == 3
    assert all(step.num_increments == 1 for case in cases for step in case.steps)


def test_generate_load_case_random_exponential_schema():
    template = mf.WorkflowTemplate.from_YAML_string(
        "name: generate_load_cases_test\n"
        "tasks:\n"
        "  - schema: generate_load_cases_random_exponential\n"
        "    inputs:\n"
        "      num_load_cases: 3\n"
    )
    task = template.tasks[0]
    output = task.all_schema_outputs[0]
    assert output.parameter.typ == "load_case"
    assert output.multiplicity == "<<input:num_load_cases>>"
    assert output.resolve_multiplicity(3) == 3

    monotonicity_output = task.all_schema_outputs[1]
    assert monotonicity_output.parameter.typ == "monotonicity"
    assert monotonicity_output.multiplicity is None


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

    # third task uses the same factory syntax for a random exponential path:
    load_case_exp = wk.tasks.define_load_case_3.elements[0].inputs.load_case.value
    args = {
        "total_time": 100,
        "num_steps": 100,
        "num_increments": 4,
        "conserve_volume": True,
        "seed": 12345,
        "max_tries": 200,
        "k_range": [0.01, 0.08],
        "delta_f_range": [-0.05, 0.05],
    }
    assert load_case_exp == LoadCase.random_exponential(**args)
    assert (
        load_case_exp
        == generate_load_cases_random_exponential(num_load_cases=1, **args)["load_case"][
            0
        ]
    )
    assert load_case_exp.num_steps == args["num_steps"]
    assert all(
        step.num_increments == args["num_increments"] for step in load_case_exp.steps
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
