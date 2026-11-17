"""Parametric normal VaR over an h-day horizon and its standard errors.

VaR = z_{1-alpha} * sigma * sqrt(h) for equally weighted or EWMA volatility
estimates, with delta-method standard errors (Table IV.6.5, Alexander 2008).
Note: ``alpha`` in this module is the tail probability (e.g. 0.01), not the
confidence level.
"""

import numpy as np
import scipy.stats as stats


def calculate_normal_var(sigma: float, h: int, alpha: float) -> float:
    """Calculates the normal linear VaR."""
    # Note: alpha here is the tail probability (e.g., 0.01 for 1%)
    z_score = stats.norm.ppf(1 - alpha)
    return z_score * sigma * np.sqrt(h)


def var_se_equally_weighted(var_estimate: float, T: int) -> float:
    """
    Approximates the standard error of a Normal VaR estimate
    using an equally weighted volatility model.
    """
    return var_estimate / np.sqrt(2 * T)


def var_se_ewma(var_estimate: float, lambda_param: float) -> float:
    """
    Approximates the standard error of a Normal VaR estimate
    using an EWMA volatility model.
    """
    return var_estimate * np.sqrt((1 - lambda_param) / (2 * (1 + lambda_param)))


def compute(returns, confidence: float = 0.99, horizon: int = 1) -> dict:
    """Standard facade: h-day parametric normal VaR from a return series.

    Estimates sigma as the sample standard deviation (ddof=1) of ``returns``
    and scales it by sqrt(horizon).

    Parameters:
    returns: 1-D array-like of historical returns (fractions).
    confidence (float): Confidence level in (0, 1), e.g. 0.99.
    horizon (int): Risk horizon in periods of the return series.

    Returns:
    dict: {"method", "confidence", "horizon", "sigma", "var"} with "var"
    expressed as a positive loss fraction.
    """
    returns = np.asarray(returns, dtype=float).ravel()
    if returns.size < 2:
        raise ValueError("returns must contain at least two observations")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in the open interval (0, 1)")
    if int(horizon) < 1:
        raise ValueError("horizon must be a positive integer")

    alpha = 1.0 - float(confidence)
    sigma = float(np.std(returns, ddof=1))
    var_pct = float(calculate_normal_var(sigma, int(horizon), alpha))
    return {
        "method": "parametric",
        "confidence": float(confidence),
        "horizon": int(horizon),
        "sigma": sigma,
        "var": var_pct,
    }


if __name__ == "__main__":
    # Example usage based on Table IV.6.5 (sigma = 0.20, h = 10, alpha = 0.01)
    sigma = 0.20
    h = 10
    alpha = 0.01

    var_10d = calculate_normal_var(sigma, h, alpha)
    se_eq_weighted = var_se_equally_weighted(var_10d, T=100)
    se_ewma = var_se_ewma(var_10d, lambda_param=0.94)
