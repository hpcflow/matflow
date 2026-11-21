import numpy as np


def simulate(x, noise=True):
    """

    Underlying relationship between flexural strength and neutron irradiation dose.
    'Perfect' relationship can be obtained by prescribing noise=False.

    """

    x = np.asarray(x)

    # baseline flexural strength (MPa)
    sigma0 = 1000

    # Model components
    hardening = 0.25 * x * np.exp(-0.5 * x)  # early radiation hardening
    low_dpa_curvature = 0.3 * x * np.exp(-x)  # slight positive concavity
    embrittlement = -0.4 * (1 - np.exp(-0.7 * x))  # long-term degradation

    # Synthetic strength model
    model_output = sigma0 * (1 + low_dpa_curvature + hardening + embrittlement)

    if noise:
        # Add noise to the model output
        try:
            model_output += np.random.normal(0, 15, size=x.shape)

        except:
            model_output += np.random.normal(0, 15)

    return {"y": model_output}
