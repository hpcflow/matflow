import numpy as np
import sklearn
from matflow.param_classes.surrogate import Surrogate


def build_surrogate(
    X_train,
    Y_train,
    parameter_names,
    n_restarts_optimizer=5,
    cross_validate=True,
    scoring="r2",
    normalize_y=True,
):
    surrogate = Surrogate(X_train, Y_train, parameter_names=parameter_names, scale=True)
    surrogate.build_model(
        n_restarts_optimizer=n_restarts_optimizer,
        cross_validate=cross_validate,
        scoring=scoring,
        normalize_y=normalize_y,
    )

    return {"surrogate": surrogate}
