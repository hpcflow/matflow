"""Test `MicrostructureSeeds`.

"""

from matflow.tests.utils import make_test_data_YAML_workflow


def test_orientations_yaml_init(null_config, tmp_path, seeds_1):
    wk = make_test_data_YAML_workflow("define_seeds.yaml", path=tmp_path)
    seeds = wk.tasks.define_microstructure_seeds.elements[
        0
    ].inputs.microstructure_seeds.value
    assert seeds == seeds_1
