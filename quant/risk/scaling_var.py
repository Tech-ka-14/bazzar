"""Square-root-of-time VaR scaling with autocorrelation adjustment.

Scales 1-day normal VaR to an h-day horizon; when returns are AR(1)
autocorrelated the effective horizon h_tilde replaces h.
Reference: Alexander (2008), Market Risk Analysis IV, Formulas
IV.1.18-IV.1.21, Example IV.1.5.
"""

import numpy as np
from scipy.stats import norm


def calculate_scaled_var(
    mu_1: float, sigma_1: float, h: int, confidence_level: float, rho: float = 0.0
):
    """
    Scales 1-day Normal VaR to an h-day horizon, adjusting for autocorrelation if present.

    Parameters:
    mu_1 (float): 1-day expected return.
    sigma_1 (float): 1-day volatility.
    h (int): Risk horizon in days.
    confidence_level (float): The confidence level (e.g., 0.99).
    rho (float): First-order autocorrelation coefficient (default is 0.0 for i.i.d).

    Returns:
    float: Scaled h-day VaR percentage.
    """
    alpha = 1.0 - confidence_level
    critical_value = norm.ppf(1 - alpha)

    # Expected return scales linearly
    mu_h = h * mu_1

    if rho == 0.0:
        # Standard Square-Root-of-Time Rule (Formula IV.1.18)
        h_tilde = h
    else:
        # Adjustment for AR(1) autocorrelation (Formula IV.1.20)
        term1 = (h - 1) * (1 - rho)
        term2 = rho * (1 - rho ** (h - 1))
        h_tilde = h + 2 * rho * (1 - rho) ** (-2) * (term1 - term2)

    # Scaled VaR calculation (Formula IV.1.21)
    scaled_var = (critical_value * np.sqrt(h_tilde) * sigma_1) - mu_h
    return scaled_var


# Example IV.1.5: 1% 10-day VaR


def compute(
    mu_1: float, sigma_1: float, h: int, confidence: float = 0.99, rho: float = 0.0
) -> dict:
    """Standard facade: scaled h-day VaR as a JSON-serializable dict.

    Parameters:
    mu_1 (float): 1-day expected return (fraction).
    sigma_1 (float): 1-day volatility (positive).
    h (int): Risk horizon in days (>= 1).
    confidence (float): Confidence level in (0, 1), e.g. 0.99.
    rho (float): First-order autocorrelation in (-1, 1).

    Returns:
    dict: {"method", "confidence", "h", "rho", "var"} with "var" the
    positive loss fraction.
    """
    if sigma_1 <= 0:
        raise ValueError("sigma_1 must be positive")
    if int(h) < 1:
        raise ValueError("h must be a positive integer")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in the open interval (0, 1)")
    if not -1.0 < rho < 1.0:
        raise ValueError("rho must be in the open interval (-1, 1)")

    var = calculate_scaled_var(float(mu_1), float(sigma_1), int(h), float(confidence), float(rho))
    return {
        "method": "sqrt_time_scaling",
        "confidence": float(confidence),
        "h": int(h),
        "rho": float(rho),
        "var": float(var),
    }


if __name__ == "__main__":
    mu_daily = 0.0
    sigma_daily = 0.015
    horizon = 10
    conf_lvl = 0.99

    var_iid = calculate_scaled_var(mu_daily, sigma_daily, horizon, conf_lvl, rho=0.0)
    var_ar1 = calculate_scaled_var(mu_daily, sigma_daily, horizon, conf_lvl, rho=0.25)

    print(f"1% 10-day VaR (i.i.d. Returns): {var_iid:.4%}")
    print(f"1% 10-day VaR (Autocorrelated rho=0.25): {var_ar1:.4%}")
