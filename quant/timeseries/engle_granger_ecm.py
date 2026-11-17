"""Engle-Granger error correction model (ECM).

Two-step Engle-Granger procedure: cointegration regression of Y on X, then
regression of Delta Y on the lagged residuals and Delta X; the residual
coefficient gamma is the speed of adjustment (mean reversion to equilibrium
when gamma < 0).
"""

import numpy as np
import statsmodels.api as sm


def fit_engle_granger_ecm(y_series, x_series):
    """
    Fits the Engle-Granger Error Correction Model to two cointegrated time series.

    y_series: Dependent time series (e.g., Asset price 1).
    x_series: Independent time series (e.g., Asset price 2).
    """
    # Step 1: Cointegration Regression (Long-run equilibrium)
    X_coint = sm.add_constant(x_series)
    coint_model = sm.OLS(y_series, X_coint).fit()

    # Extract the long-run residual (error term)
    residuals = coint_model.resid

    # Step 2: Error Correction Mechanism (ECM) Regression
    # Create variables for the ECM: Delta(Y), lagged Residuals, Delta(X)
    delta_y = y_series.diff().dropna()
    delta_x = x_series.diff().dropna()

    # Align lagged residuals with the differences
    lagged_residuals = residuals.shift(1).dropna()

    # Ensure all arrays are the same length
    min_len = min(len(delta_y), len(delta_x), len(lagged_residuals))
    delta_y = delta_y[-min_len:]
    lagged_residuals = lagged_residuals[-min_len:]
    delta_x = delta_x[-min_len:]

    # Build the ECM design matrix: [Constant, Lagged_Residuals, Delta_X]
    X_ecm = np.column_stack((np.ones(min_len), lagged_residuals, delta_x))

    ecm_model = sm.OLS(delta_y, X_ecm).fit()

    return {
        "Cointegration Beta": coint_model.params.iloc[1],
        "Speed of Adjustment (gamma)": ecm_model.params[1],
        "ECM Coefficient on Delta X": ecm_model.params[2],
        "ECM R-Squared": ecm_model.rsquared,
    }


def compute(y_series, x_series) -> dict:
    """Standard facade: Engle-Granger ECM estimates as a JSON dict.

    Parameters:
    y_series: 1-D array-like of the dependent series (e.g. asset price 1).
    x_series: 1-D array-like of the independent series, same length (>= 5).

    Returns:
    dict: {"cointegration_beta", "speed_of_adjustment",
    "delta_x_coefficient", "ecm_r_squared", "mean_reverting"} with plain
    floats/bools; mean_reverting is True when the gamma estimate is < 0.
    """
    y = np.asarray(y_series, dtype=float).ravel()
    x = np.asarray(x_series, dtype=float).ravel()
    if y.size < 5 or y.size != x.size:
        raise ValueError("y_series and x_series must have equal length >= 5")

    import pandas as pd

    results = fit_engle_granger_ecm(pd.Series(y), pd.Series(x))
    gamma = float(results["Speed of Adjustment (gamma)"])
    return {
        "cointegration_beta": float(results["Cointegration Beta"]),
        "speed_of_adjustment": gamma,
        "delta_x_coefficient": float(results["ECM Coefficient on Delta X"]),
        "ecm_r_squared": float(results["ECM R-Squared"]),
        "mean_reverting": bool(gamma < 0.0),
    }


# Example Usage:
# ecm_results = fit_engle_granger_ecm(asset_A_prices, asset_B_prices)
