"""Standard error of a simulation/historical VaR quantile estimate.

Approximates the standard error of an empirical quantile via the density
at the quantile: SE = (1/f(q)) * sqrt(alpha (1 - alpha) / T).
Reference: Alexander (2008), Market Risk Analysis IV, Example IV.6.4.
"""

import numpy as np
import scipy.stats as stats


def quantile_var_se(alpha: float, T: int, quantile_val: float, h: int, sigma_daily: float) -> float:
    """
    Approximates the standard error of a Simulation/Historical VaR quantile.
    This requires evaluating the Probability Density Function (PDF) at the quantile.

    For demonstration, we evaluate the PDF assuming the underlying true distribution
    is Normal with mean 0 and standard deviation scaled for h days.
    """
    # True h-day standard deviation
    sigma_h = sigma_daily * np.sqrt(h)

    # Evaluate the PDF f(x) at the quantile value
    # Note: VaR is typically positive, but the actual quantile value is negative
    f_q = stats.norm.pdf(-quantile_val, loc=0, scale=sigma_h)

    # Calculate standard error
    se = (1 / f_q) * np.sqrt((alpha * (1 - alpha)) / T)
    return se


# Example usage from Example IV.6.4


def compute(alpha: float, T: int, quantile_val: float, h: int, sigma_daily: float) -> dict:
    """Standard facade: VaR quantile standard error as a JSON dict.

    Parameters:
    alpha (float): Tail probability in (0, 1), e.g. 0.01.
    T (int): Number of simulated/historical scenarios (positive).
    quantile_val (float): VaR estimate expressed as a positive loss.
    h (int): Risk horizon in days (positive).
    sigma_daily (float): Daily volatility of the assumed underlying
    normal distribution (positive).

    Returns:
    dict: {"method", "alpha", "n", "standard_error"}.
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")
    if int(T) <= 0 or int(h) <= 0:
        raise ValueError("T and h must be positive")
    if sigma_daily <= 0:
        raise ValueError("sigma_daily must be positive")

    se = quantile_var_se(float(alpha), int(T), float(quantile_val), int(h), float(sigma_daily))
    return {
        "method": "quantile_se",
        "alpha": float(alpha),
        "n": int(T),
        "standard_error": float(se),
    }


if __name__ == "__main__":
    var_10d = 0.025  # example 10-day 99% VaR estimate
    var_quantile_se = quantile_var_se(
        alpha=0.01, T=1000, quantile_val=var_10d, h=10, sigma_daily=0.20
    )
