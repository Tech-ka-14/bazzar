"""ARIMA(p, d, q) forecasting.

Fits an ARIMA model to a univariate time series and produces out-of-sample
point forecasts together with the AIC/BIC information criteria.
"""

import warnings

import numpy as np
from statsmodels.tsa.arima.model import ARIMA


def fit_and_forecast_arima(time_series, order=(1, 1, 1), steps_ahead=5):
    """
    Fits an ARIMA(p,d,q) model to the data and generates out-of-sample forecasts.
    order: A tuple of (p, d, q)
    """
    warnings.filterwarnings("ignore")  # Ignore convergence warnings for simplicity
    # Initialize and fit the ARIMA model
    model = ARIMA(time_series, order=order)
    fitted_model = model.fit()

    # Generate forecast
    forecast = fitted_model.forecast(steps=steps_ahead)

    # Extract model summary metrics
    aic = fitted_model.aic
    bic = fitted_model.bic

    return {
        "Model Summary": fitted_model.summary().tables[1],
        "AIC": aic,
        "BIC": bic,
        "Forecast": forecast,
    }


def compute(time_series, order=(1, 1, 1), steps_ahead: int = 5) -> dict:
    """Standard facade: ARIMA fit and forecast as a JSON-serializable dict.

    Parameters:
    time_series: 1-D array-like of observations.
    order (tuple): (p, d, q) ARIMA order.
    steps_ahead (int): Number of out-of-sample steps to forecast (>= 1).

    Returns:
    dict: {"order", "steps_ahead", "aic", "bic", "forecast"} with the
    forecast as a list of plain floats.
    """
    steps_ahead = int(steps_ahead)
    if steps_ahead < 1:
        raise ValueError("steps_ahead must be at least 1")
    if len(tuple(order)) != 3:
        raise ValueError("order must be a (p, d, q) tuple of length 3")

    results = fit_and_forecast_arima(time_series, order=tuple(order), steps_ahead=steps_ahead)
    return {
        "order": [int(p) for p in order],
        "steps_ahead": steps_ahead,
        "aic": float(results["AIC"]),
        "bic": float(results["BIC"]),
        "forecast": [float(x) for x in np.asarray(results["Forecast"], dtype=float).ravel()],
    }


# Example usage
# arima_results = fit_and_forecast_arima(prices, order=(2, 1, 1), steps_ahead=10)
