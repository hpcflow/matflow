import numpy as np
import sklearn
from matflow.param_classes.surrogate import Surrogate


def build_surrogate(
    X_train,
    Y_train,
    parameter_names,
    n_restarts_optimizer,
    cross_validate,
    scoring,
    normalize_y,
    validate,
    X_test,
    Y_test,
):
    surrogate = Surrogate(X_train, Y_train, parameter_names=parameter_names, scale=True)
    surrogate.build_model(
        n_restarts_optimizer=n_restarts_optimizer,
        cross_validate=cross_validate,
        scoring=scoring,
        normalize_y=normalize_y,
    )

    # validation:
    vld_out = {}
    if validate:
        Y_prediction, Y_error = surrogate.make_prediction(X_test, return_std=True)
        score = sklearn.metrics.r2_score(Y_test, Y_prediction)
        print(f"Validation score: {score}.")
        vld_out = {
            "Y_prediction": Y_prediction,
            "Y_error": Y_error,
            "score": score,
        }

    # versions: once serialised, the model (e.g. GaussianProcessRegressor) may not be
    # correctly deserialised when using different versions of scikit-learn and its
    # dependencies:
    versions = {
        "numpy": np.__version__,
        "sklearn": sklearn.__version__,
    }

    return {"surrogate": surrogate, "validation": vld_out, "versions": versions}
