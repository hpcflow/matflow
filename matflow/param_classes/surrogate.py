"""
Surrogate model building, fitting, and Bayesian inference with Scikit-learn and PyMC.

Note: some methods of the Surrogate class require additional dependencies that are not
included by MatFlow; namely: sklearn, pytensor, pymc, and on Windows, sklearnex.

This code is taken entirely (with minor modifications) from:
https://github.com/LightForm-group/surrogatetools.

Some imports (including skops.io, scipy.stats, and scipy.optimize) are inlined into the
methods where they are needed to reduce the effect on MatFlow's import time.

"""

from __future__ import annotations
from typing import ClassVar
import numpy as np
from hpcflow.sdk.core.parameters import ParameterValue

import matflow as mf


class Surrogate(ParameterValue):

    _typ: ClassVar[str] = "surrogate"

    #: Whether we have yet patched scikit-learn with the Intel extension package.
    _is_patched: ClassVar[bool] = False

    #: Path to the c++ compiler that Pytensor should use. If setting, this should be done
    #: before an instance is created.
    pytensor_config_cxx: ClassVar[str | None] = None

    #: Whether we have yet configured Pytensor's cxx config option.
    _pytensor_config_cxx_is_set: ClassVar[bool] = False

    def __init__(self, X, y, parameter_names=None, model=None, scale=True):

        self._patch_once()

        self.X_scaler = None
        self.y_scaler = None

        self.X = X
        self.y = y

        self.parameter_range = np.array(
            [np.min(self.X, axis=0), np.max(self.X, axis=0)]
        ).T

        self.parameter_names = parameter_names

        self.N, self.D = self.X.shape
        self.N, self.P = self.y.shape

        if model:
            trusted = [
                "sklearn.gaussian_process.kernels.ConstantKernel",
                "sklearn.gaussian_process.kernels.Matern",
                "sklearn.gaussian_process.kernels.Product",
                "sklearn.gaussian_process.kernels.Sum",
            ]
            import skops.io as sio

            self.model = sio.loads(model, trusted=trusted)
        else:
            self.model = None

        self._scale = scale
        if scale:
            self.scale_data()

    def _serialise_model(self) -> bytes:
        """Serialise the scikit-learn model to bytes using skops."""

        if model := self.model:
            import skops.io as sio

            return sio.dumps(model)

        else:
            return None

    def to_dict(self):
        """Convert to a serialisable dictionary."""
        X, y = self.get_unscaled_data() if self._scale else (self.X, self.y)
        return {
            "X": X,
            "y": y,
            "parameter_names": self.parameter_names,
            "model": self._serialise_model(),
            "scale": self._scale,
        }

    def scale_data(self, scale_X=True, scale_y=True):

        from sklearn.preprocessing import RobustScaler

        if self.X_scaler == None:
            self.X_scaler = RobustScaler().fit(self.X)

        if self.y_scaler == None:
            self.y_scaler = RobustScaler().fit(self.y)

        if scale_X == True:
            self.X = self.X_scaler.transform(self.X)

        if scale_y == True:
            self.y = self.y_scaler.transform(self.y)

        return None

    def get_unscaled_data(self, unscale_X=True, unscale_y=True):

        un_X = None
        if unscale_X:
            un_X = self.X_scaler.inverse_transform(self.X)

        un_y = None
        if unscale_y:
            un_y = self.y_scaler.inverse_transform(self.y)

        return un_X, un_y

    @classmethod
    def _patch_once(cls):
        if not cls._is_patched:
            if mf.run_time_info.platform != "macos":
                from sklearnex import patch_sklearn

                patch_sklearn()
            cls._is_patched = True

    def build_model(
        self,
        kernel="matern",
        cross_validate=False,
        cross_validator=5,
        scoring="neg_mean_absolute_error",
        **kwargs,
    ):

        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import Matern
        from sklearn.model_selection import cross_val_score

        # Firstly we define the kernel to be used
        if kernel == "matern":
            kernel = 1.0 * Matern(length_scale=self.D * [1], nu=2.5) + 1.0

        else:
            kernel = kernel

        # Build the kernel along with any additional parameters

        # Optimise with cross validation
        if cross_validate == True:

            model = GaussianProcessRegressor(kernel=kernel, **kwargs)
            score = cross_val_score(
                model, self.X, self.y, cv=cross_validator, scoring=scoring
            )

            print("Cross validation score: ", np.round(score, 2))

        self.model = GaussianProcessRegressor(kernel=kernel, **kwargs)
        self.model.fit(self.X, self.y)

    def make_prediction(self, X, return_std=False, scalar_output=False):

        if self.X_scaler is not None:
            X = self.X_scaler.transform(X)

        y_prediction, y_error = self.model.predict(X, return_std=True)

        if scalar_output == True:
            y_prediction = y_prediction.reshape(1, -1)

        if self.y_scaler is not None:
            y_prediction = self.y_scaler.inverse_transform(y_prediction)
            y_error = y_error * self.y_scaler.scale_

        if return_std:
            return y_prediction, y_error
        else:
            return y_prediction

    def make_prediction_sobol(self, X):

        X = np.array(X).T

        y_prediction = self.make_prediction(X, return_std=False)

        return y_prediction.T

    def generate_sobol(self, use_fit=False, **kwargs):
        """
        Wrapper function for scipy.stats.sobol_indices

        Args:
            n (int): number of samples

            **kwargs: additonal parameters

        Returns:
            sobol: SobolResult
        """

        from scipy.stats import norm, uniform, sobol_indices

        if use_fit == True:
            distributions = [
                norm(loc=self.parameter_mean[i], scale=self.parameter_std[i])
                for i in range(len(self.parameter_range))
            ]

        else:
            distributions = [
                uniform(loc=x[0], scale=x[1] - x[0]) for x in self.parameter_range
            ]

        sobol = sobol_indices(
            func=self.make_prediction_sobol, dists=distributions, **kwargs
        )

        return sobol

    def fit(self, Y_actual, Y_error, use_std=True, **kwargs):
        from scipy.optimize import shgo

        def _loss(params, Y_actual, Y_error):

            params = np.array(params).reshape(1, -1)

            if use_std == True:

                y_prediction, y_prediction_error = self.make_prediction(
                    X=params, return_std=True
                )

                residual_square = (
                    y_prediction[0] - Y_actual
                ) ** 2 + y_prediction_error**2

            else:
                y_prediction = self.make_prediction(X=params)

                residual_square = (y_prediction[0] - Y_actual) ** 2

            error_residual_square = Y_error**2

            loss = residual_square / error_residual_square

            return loss.sum()

        res = shgo(_loss, bounds=self.parameter_range, args=(Y_actual, Y_error), **kwargs)

        return res

    def _config_pytensor_once(self):
        """
        Configure the path to the C++ compiler that pytensor should use, using the
        class variable `pytensor_config_cxx` if set, or, if on Apple silicon, setting to a
        sensible default.
        """

        if self._pytensor_config_cxx_is_set:
            return

        import pytensor

        if (pt_cxx := self.pytensor_config_cxx) is not None:
            pytensor.config.cxx = pt_cxx
        elif mf.run_time_info.is_apple_silicon:
            pytensor.config.cxx = "/usr/bin/clang++"

        self._pytensor_config_cxx_is_set = True

    def perform_inference(self, Y_actual, Y_error, initval=None, use_std=True, **kwargs):

        self._config_pytensor_once()
        import pymc as pm
        import pytensor.tensor as pt
        from pytensor.graph import Apply, Op

        data = [Y_actual, Y_error]

        def my_loglike(params, data):
            # We fail explicitly if inputs are not numerical types for the sake of this tutorial
            # As defined, my_loglike would actually work fine with PyTensor variables!
            params = np.array(params).reshape(1, -1)

            y_actual, y_actual_error = data

            # The surrogate must provide a prediction and uncertainty estimate
            if use_std == True:
                y_prediction, y_prediction_error = self.make_prediction(
                    params, return_std=True
                )

                residual_square = (y_prediction[0] - y_actual) ** 2 + y_prediction_error[
                    0
                ] ** 2

            else:
                y_prediction = self.make_prediction(params)

                residual_square = (y_prediction[0] - y_actual) ** 2

            loss = residual_square / y_actual_error**2

            f = -0.5 * loss

            return f

        class LogLike(Op):
            def make_node(self, params, data) -> Apply:
                # Convert inputs to tensor variables
                params = pt.as_tensor(params)
                data = pt.as_tensor(data)

                inputs = [params, data]
                # Define output type, in our case a vector of likelihoods
                # with the same dimensions and same data type as data
                # If data must always be a vector, we could have hard-coded
                outputs = [pt.vector()]

                # Apply is an object that combines inputs, outputs and an Op (self)
                return Apply(self, inputs, outputs)

            def perform(
                self, node: Apply, inputs: list[np.ndarray], outputs: list[list[None]]
            ) -> None:
                # This is the method that compute numerical output
                # given numerical inputs. Everything here is numpy arrays
                params, data = inputs  # this will contain my variables

                # call our numpy log-likelihood function
                loglike_eval = my_loglike(params, data)

                # Save the result in the outputs list provided by PyTensor
                # There is one list per output, each containing another list
                # pre-populated with a `None` where the result should be saved.
                outputs[0][0] = np.asarray(loglike_eval)

        loglike_op = LogLike()

        def custom_dist_loglike(data, params):

            # create our Op
            # data, or observed is always passed as the first input of CustomDist
            return loglike_op(params, data)

        # use PyMC to sampler from log-likelihood
        with pm.Model() as no_grad_model:

            params = []

            for i in range(self.D):

                distribution = pm.Uniform(
                    self.parameter_names[i],
                    lower=self.parameter_range[i][0],
                    upper=self.parameter_range[i][1],
                    initval=initval[i],
                )

                params.append(distribution)

            # use a CustomDist with a custom logp function
            likelihood = pm.CustomDist(
                "likelihood",
                params,
                observed=data,
                logp=custom_dist_loglike,
            )

        ip = no_grad_model.initial_point()

        no_grad_model.compile_logp(vars=[likelihood], sum=False)(ip)

        with no_grad_model:

            step = pm.DEMetropolisZ()

            # Use custom number of draws to replace the HMC based defaults
            idata_no_grad = pm.sample(
                step=step, **kwargs
            )  # 50_000, tune=50_000,cores=4,chains=4,step=step,return_inferencedata=True)

        return idata_no_grad
