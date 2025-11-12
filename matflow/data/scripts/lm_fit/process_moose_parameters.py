def process_moose_parameters(p_perturbed, p_scales, index):
    # print(f"process_moose_parameters: {p_perturbed[:]=!r}")
    # print(f"process_moose_parameters: {p_scales[:]=!r}")

    E, nu = [i * j for i, j in zip(p_scales, p_perturbed[index])]
    # print(f"process_moose_parameters: {E=!r}; {nu=!r}")
    return {"elasticity": {"youngs_modulus": E, "poissons_ratio": nu}}
