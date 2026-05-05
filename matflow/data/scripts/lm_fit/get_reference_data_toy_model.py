import numpy as np


def model_exp(x, *p):
    a, b, c = p
    return a * np.exp(b * x) + c


def get_reference_data_toy_model(p_true):
    # print(f"get_reference_data_toy_model: {p_true=!r}")
    np.random.seed(0)
    x_data = np.linspace(0, 2, 30)
    y_clean = model_exp(x_data, *p_true)
    y_ref = y_clean + 0.12 * np.random.randn(x_data.size)  # add noise
    return {"x": x_data, "reference_response": y_ref}
