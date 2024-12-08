"""Test `Orientations` and related classes.

"""

from matflow.tests.utils import make_test_data_YAML_workflow


def test_orientations_yaml_init(null_config, tmp_path, orientations_1):
    wk = make_test_data_YAML_workflow("define_orientations.yaml", path=tmp_path)
    orientations = wk.tasks.define_orientations.elements[0].inputs.orientations.value
    assert orientations == orientations_1
