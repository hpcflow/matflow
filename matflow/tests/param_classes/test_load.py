from pathlib import Path

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
