"""EWMA normal linear Value at Risk (RiskMetrics).

VaR = z_{1-alpha} * sigma_t * sqrt(h) * V, where sigma_t is the current EWMA
daily volatility, h the horizon in days and V the portfolio value
(Equation IV.2.82, Alexander 2008).
"""

import numpy as np
from scipy.stats import norm

from quant.timeseries.ewma_variance_volatility import calculate_ewma_variance


def calculate_ewma_var(
    current_ewma_vol_daily: float,
    portfolio_value: float,
    alpha: float = 0.01,
    horizon_days: int = 10,
) -> float:
    """
    Calculates the short-term EWMA Normal Linear VaR (Equation IV.2.82).
    """
    # Standard normal critical value
    critical_value = norm.ppf(1 - alpha)

    # Scale daily volatility to h-day horizon
    volatility_h = current_ewma_vol_daily * np.sqrt(horizon_days)

    # Calculate VaR
    var_estimate = critical_value * volatility_h * portfolio_value

    return var_estimate


def compute(
    returns,
    lambda_param: float = 0.94,
    confidence: float = 0.99,
    horizon_days: int = 1,
    portfolio_value: float = 1.0,
) -> dict:
    """Standard facade: EWMA VaR from a return series.

    Runs the EWMA variance recursion (see
    ``quant.timeseries.ewma_variance_volatility``) to obtain the current
    daily volatility, then applies the EWMA normal linear VaR formula.

    Parameters:
    returns: 1-D array-like of historical returns (fractions).
    lambda_param (float): EWMA smoothing constant in (0, 1), e.g. 0.94.
    confidence (float): Confidence level in (0, 1), e.g. 0.99.
    horizon_days (int): Risk horizon in days.
    portfolio_value (float): Nominal portfolio value for the monetary VaR.

    Returns:
    dict: {"method", "confidence", "lambda", "horizon_days",
    "current_volatility", "var", "var_value"}.
    """
    returns = np.asarray(returns, dtype=float).ravel()
    if returns.size < 2:
        raise ValueError("returns must contain at least two observations")
    if not 0.0 < lambda_param < 1.0:
        raise ValueError("lambda_param must be in the open interval (0, 1)")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in the open interval (0, 1)")

    alpha = 1.0 - float(confidence)
    ewma_variances = calculate_ewma_variance(returns, float(lambda_param))
    current_vol = float(np.sqrt(ewma_variances[-1]))
    var_value = float(
        calculate_ewma_var(current_vol, float(portfolio_value), alpha, int(horizon_days))
    )
    return {
        "method": "ewma",
        "confidence": float(confidence),
        "lambda": float(lambda_param),
        "horizon_days": int(horizon_days),
        "current_volatility": current_vol,
        "var": var_value / float(portfolio_value),
        "var_value": var_value,
    }


if __name__ == "__main__":
    # Using the RiskMetrics framework for a $1,000,000 portfolio
    current_daily_volatility = np.sqrt(0.00015)  # Example derived from an EWMA process
    confidence_lvl = 0.01  # 1% VaR
    horizon = 10  # 10-Day VaR

    ewma_var = calculate_ewma_var(
        current_ewma_vol_daily=current_daily_volatility,
        portfolio_value=1_000_000,
        alpha=confidence_lvl,
        horizon_days=horizon,
    )

    print(f"1% 10-Day EWMA VaR: ${ewma_var:,.0f}")
