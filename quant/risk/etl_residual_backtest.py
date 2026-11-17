"""ETL backtest via standardized exceedance residuals.

On days where the realized loss exceeds the VaR forecast, the
Standardized Exceedance Residual is SER = (-y - ETL) / sigma; the mean
SER is tested with a pseudo t-statistic (zero under a correct ETL
forecast).
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.6.4.
"""

import numpy as np


def calculate_etl_exceedance_residuals(
    returns: np.ndarray,
    var_forecasts: np.ndarray,
    etl_forecasts: np.ndarray,
    volatility_forecasts: np.ndarray,
) -> np.ndarray:
    """
    Isolates days where losses exceed VaR and calculates the
    Standardized Exceedance Residuals (SER).
    """
    # Find indices where realized loss exceeds the forecasted VaR
    # Note: Assuming returns are standard percentages (e.g., -0.05 is a 5% loss)
    # and VaR is expressed as a positive percentage (e.g., 0.03 for 3% VaR)
    exceedance_mask = returns < -var_forecasts

    # Isolate the data for exceedance days
    y_exceed = returns[exceedance_mask]
    etl_exceed = etl_forecasts[exceedance_mask]
    vol_exceed = volatility_forecasts[exceedance_mask]

    # Calculate SER
    ser = (-y_exceed - etl_exceed) / vol_exceed
    return ser


def etl_mean_residual_test(ser: np.ndarray) -> tuple:
    """
    Calculates the pseudo t-statistic for the ETL residuals.
    """
    mean_ser = np.mean(ser)
    std_ser = np.std(ser, ddof=1)
    n_exceedances = len(ser)

    standard_error = std_ser / np.sqrt(n_exceedances)
    t_stat = mean_ser / standard_error

    return mean_ser, t_stat


def compute(returns, var_forecasts, etl_forecasts, volatility_forecasts) -> dict:
    """Standard facade: ETL residual backtest as a JSON-serializable dict.

    Parameters:
    returns: 1-D array-like of realized returns (fractions).
    var_forecasts: Positive VaR forecasts aligned with returns.
    etl_forecasts: Positive ETL forecasts aligned with returns.
    volatility_forecasts: Volatility forecasts aligned with returns.

    Returns:
    dict: {"method", "n", "n_exceedances", "mean_ser", "t_stat"}.
    """
    returns = np.asarray(returns, dtype=float).ravel()
    var_f = np.asarray(var_forecasts, dtype=float).ravel()
    etl_f = np.asarray(etl_forecasts, dtype=float).ravel()
    vol_f = np.asarray(volatility_forecasts, dtype=float).ravel()
    if not (returns.size == var_f.size == etl_f.size == vol_f.size):
        raise ValueError("all input series must have equal length")
    if returns.size == 0:
        raise ValueError("returns must contain at least one observation")

    ser = calculate_etl_exceedance_residuals(returns, var_f, etl_f, vol_f)
    if ser.size == 0:
        raise ValueError("no VaR exceedances found; ETL backtest is undefined")
    mean_ser, t_stat = etl_mean_residual_test(ser)
    return {
        "method": "etl_residual_test",
        "n": int(returns.size),
        "n_exceedances": int(ser.size),
        "mean_ser": float(mean_ser),
        "t_stat": float(t_stat),
    }
