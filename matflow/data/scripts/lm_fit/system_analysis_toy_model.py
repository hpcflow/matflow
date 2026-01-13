import numpy as np


def model_exp(x, *p):
    # print(f"model_exp: {p}")
    a, b, c = p
    return a * np.exp(b * x) + c


def system_analysis_toy_model(x, p_perturbed, index, p_scales):
    # print(f"system_analysis_toy_model: {x=!r}")
    # print(f"system_analysis_toy_model: {p_perturbed[index]=!r}")
    # print(f"system_analysis_toy_model: {p_scales[:]=!r}")
    # print(f"system_analysis_toy_model: {index=!r}")
    return {
        "system_response": model_exp(
            x, *(i * j for i, j in zip(p_scales, p_perturbed[index]))
        )
    }
