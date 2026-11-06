"""MATLAB plotting regression; requires a configured matlab_env in integration runs."""
from pathlib import Path

import numpy as np
from PIL import Image
import pytest
import yaml

import matflow as mf


@pytest.mark.integration
@pytest.mark.parametrize("method", ["pole_figure", "inverse_pole_figure"])
def test_matlab_plot_quaternion_component_order(tmp_path: Path, method: str):
    q = np.random.default_rng(783).normal(size=(12, 4))
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    tasks = []
    for order in ["scalar_vector", "vector_scalar"]:
        inputs = {
            "orientations": {
                "data": (
                    q if order == "scalar_vector" else np.roll(q, -1, axis=1)
                ).tolist(),
                "representation": {"type": "quaternion", "quat_order": order},
                "unit_cell_alignment": {"x": "a", "y": "b", "z": "c"},
            },
            "crystal_symmetry": "cubic",
            "execution_mode": "script",
            "use_contours": False,
        }
        if method == "pole_figure":
            inputs["pole_figure_directions"] = [[0, 0, 1], [1, 1, 1]]
        else:
            inputs["IPF_reference_directions"] = ["x", "z"]
        tasks.append(
            {"schema": f"visualise_orientations_{method}_mtex", "inputs": inputs}
        )
    template = mf.WorkflowTemplate.from_YAML_string(
        yaml.safe_dump(
            {
                "name": "matlab_quaternion_order",
                "resources": {"any": {"random_seed": 1234}},
                "tasks": tasks,
            }
        )
    )
    workflow = mf.Workflow.from_template(template, path=tmp_path)
    workflow.submit(wait=True, add_to_known=False)
    runs = mf.Workflow(workflow.path).get_all_EARs()
    assert all(run.status.name == "success" for run in runs)
    label = (
        "mtex_pole_figures" if method == "pole_figure" else "mtex_inverse_pole_figures"
    )
    paths = [getattr(run.output_files, label).value for run in runs]
    with Image.open(paths[0]) as first, Image.open(paths[1]) as second:
        np.testing.assert_array_equal(np.asarray(first), np.asarray(second))
