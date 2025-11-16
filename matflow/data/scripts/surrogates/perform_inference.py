def perform_inference(
    surrogate,
    Y_test,
    test_index,
    test_error,
    draws,
    tune,
    chains,
    cores,
    fitted_x,
    use_std,
):
    data = Y_test[test_index]
    error = test_error * data

    inf_dat = surrogate.perform_inference(
        Y_actual=data,
        Y_error=error,
        draws=draws,
        tune=tune,
        chains=chains,
        cores=cores,
        return_inferencedata=True,
        initval=fitted_x,
        use_std=use_std,
    )

    return {"inference_data": inf_dat}
