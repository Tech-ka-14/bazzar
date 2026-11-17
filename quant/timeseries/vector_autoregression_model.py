"""Vector Autoregression (VAR) model fitting.

Fits a VAR(p) to stationary multivariate returns with the lag order selected
by the Akaike Information Criterion (AIC) up to a maximum lag.
"""

import numpy as np
from statsmodels.tsa.api import VAR


def fit_var_model(stationary_returns, max_lags=5):
    """
    Fits a Vector Autoregression (VAR) model to a DataFrame of stationary returns
    and determines the optimal lag length using the Akaike Information Criterion (AIC).
    """
    # Initialize the VAR model
    model = VAR(stationary_returns)

    # Fit the model, allowing statsmodels to select the optimal lag up to max_lags
    fitted_var = model.fit(maxlags=max_lags, ic="aic")

    # Extract the optimal lag order chosen by the AIC
    optimal_lag = fitted_var.k_ar

    return {
        "Optimal Lags (p)": optimal_lag,
        "Coefficient Matrices (Phi)": fitted_var.coefs,
        "Intercepts (Alpha)": fitted_var.intercept,
        "Residual Covariance": fitted_var.sigma_u,
        "Model Summary": fitted_var.summary(),
    }


def compute(stationary_returns, max_lags: int = 5) -> dict:
    """Standard facade: AIC-selected VAR fit as a JSON-serializable dict.

    Parameters:
    stationary_returns: 2-D array-like (T observations x k variables) or a
    pandas DataFrame of stationary returns.
    max_lags (int): Maximum lag order considered by the AIC selection (>= 0).

    Returns:
    dict: {"optimal_lags", "n_variables", "coefficient_matrices",
    "intercepts", "residual_covariance"} with plain lists/floats/ints.
    """
    max_lags = int(max_lags)
    if max_lags < 0:
        raise ValueError("max_lags must be non-negative")

    results = fit_var_model(stationary_returns, max_lags=max_lags)
    coefs = np.asarray(results["Coefficient Matrices (Phi)"], dtype=float)
    return {
        "optimal_lags": int(results["Optimal Lags (p)"]),
        "n_variables": int(coefs.shape[-1]) if coefs.ndim >= 2 else 0,
        "coefficient_matrices": coefs.tolist(),
        "intercepts": np.asarray(results["Intercepts (Alpha)"], dtype=float).tolist(),
        "residual_covariance": np.asarray(results["Residual Covariance"], dtype=float).tolist(),
    }


# Example Usage:
# Assuming 'portfolio_returns' is a strictly stationary Pandas DataFrame of asset returns
# var_results = fit_var_model(portfolio_returns, max_lags=10)
