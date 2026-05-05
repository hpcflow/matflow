from matflow.param_classes import SingleCrystalParameters


def test_perturbation():
    params = SingleCrystalParameters(
        phases={"Al": {"xi_0_sl": [30e6]}},
        perturbations={"path": ["Al", "xi_0_sl", 0], "multiplicative": 1.05},
    )
    assert params.phases == {"Al": {"xi_0_sl": [30e6 * 1.05]}}


def test_perturbation_list():
    params = SingleCrystalParameters(
        phases={"Al": {"xi_0_sl": [30e6]}},
        perturbations=[
            {"path": ["Al", "xi_0_sl", 0], "multiplicative": 1.05},
            {"path": ["Al", "xi_0_sl", 0], "multiplicative": 1.05},
        ],
    )
    assert params.phases == {"Al": {"xi_0_sl": [30e6 * 1.05 * 1.05]}}


def test_perturbation_init_to_dict():
    params = SingleCrystalParameters(
        phases={"Al": {"xi_0_sl": [30e6]}},
        perturbations={"path": ["Al", "xi_0_sl", 0], "multiplicative": 1.05},
    )
    SingleCrystalParameters(**params.to_dict())
