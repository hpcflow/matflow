import numpy as np
import scipy


def collate_CP_data(VE_response, workflow):

    # Path variable names
    paths = (
        workflow.tasks.simulate_VE_loading_damask.template.element_sets[0]
        .multi_path_sequences[0]
        .paths
    )

    # We assume the final section of parameters is the appropriate variable name
    fitting_param_names = [path.split("plastic.")[-1] for path in paths]

    # Determine the scaling used, either linear or logarithmic
    scale = [
        workflow.tasks.simulate_VE_loading_damask.template.element_sets[0]
        .multi_path_sequences[0]
        ._values_method_args["bounds"][path]["scaling"]
        for path in paths
    ]

    # Now determine the bounds of the parameter space
    bounds = [
        workflow.tasks.simulate_VE_loading_damask.template.element_sets[0]
        .multi_path_sequences[0]
        ._values_method_args["bounds"][path]["extent"]
        for path in paths
    ]

    # Now apply the log or linear transformations to the bounds
    bounds = [
        np.log10(bounds[i]) if scale[i] == "log" else bounds[i]
        for i in range(len(bounds))
    ]

    X = np.linspace(0.0, 0.09, 150)
    y_simulation = []
    theta = []

    for VE_idx, VE_resp_i in enumerate(VE_response):

        element = workflow.tasks.simulate_VE_loading_damask.elements[VE_idx]

        try:

            # Read the parameters
            params = [element.get(path) for path in paths]

            # Scale the parameters
            scaled_params = [
                np.log10(params[i]) if scale[i] == "log" else params[i]
                for i in range(len(params))
            ]

            # Extract the stress strain curves
            true_stress_tensor = np.asarray(
                VE_resp_i["phase_data"]["vol_avg_equivalent_stress"]["data"]
            )
            true_strain_tensor = np.asarray(
                VE_resp_i["phase_data"]["vol_avg_equivalent_strain"]["data"]
            )

            stress = true_stress_tensor[:, 0, 0]
            strain = true_strain_tensor[:, 0, 0]

            f_stress = scipy.interpolate.interp1d(x=strain, y=stress)

            # save the outputs
            y_simulation.append(f_stress(X))

            # Save the parameters
            theta.append(scaled_params)

        except Exception as e:
            print("Read Error:", e)
            y_simulation.append(np.zeros_like(X))
            theta.append(scaled_params)

    return {
        "y_simulation": np.array(y_simulation),
        "theta": np.array(theta),
        "parameter_names": fitting_param_names,
    }
