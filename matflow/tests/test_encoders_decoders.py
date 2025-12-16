import pytest
import numpy as np
import matflow as mf


@pytest.mark.xfail(reason="Requires the Arviz (Bayesian inference) package.")
def test_encode_decode_arviz_inference_data(null_config, tmp_path):

    import arviz

    p1 = np.array([1, 2, 3])
    p2 = (1, 2, 3)
    s1 = mf.TaskSchema(
        "t1",
        inputs=[
            mf.SchemaInput("inference_data"),
            mf.SchemaInput("p1"),
            mf.SchemaInput("p2"),
        ],
    )
    t1 = mf.Task(
        schema=s1,
        inputs={
            "inference_data": {"a": arviz.data.inference_data.InferenceData()},
            "p1": p1,
            "p2": p2,
        },
    )
    wk = mf.Workflow.from_template_data(
        template_name="test",
        tasks=[t1],
        store="zarr",
        path=tmp_path,
    )

    assert isinstance(
        wk.tasks[0].elements[0].inputs.inference_data.value["a"], arviz.InferenceData
    )
    assert np.allclose(wk.tasks[0].elements[0].inputs.p1.value, p1)
    assert wk.tasks[0].elements[0].inputs.p2.value == p2
