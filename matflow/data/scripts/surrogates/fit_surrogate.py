def fit_surrogate(surrogate, Y_test, test_index, test_error, iters, n, use_std):

    data = Y_test[test_index]
    error = test_error * data

    res = surrogate.fit(
        Y_actual=data,
        Y_error=error,
        iters=iters,
        n=n,
        use_std=use_std,
    )
    print(f"Fitted parameters: {res.x}")
    return {"fitted_x": res.x, "optimize_result": dict(res)}
