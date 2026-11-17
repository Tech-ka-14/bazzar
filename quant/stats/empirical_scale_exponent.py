"""Empirical power-law scale exponent of risk quantiles.

Estimates the exponent 1/xi in quantile_h = quantile_1 * h^(1/xi) via a
through-origin log-log regression (Equation IV.3.2). Reference: Alexander
(2008), Vol. IV, Example IV.3.2.4.
"""

import numpy as np
import statsmodels.api as sm


def estimate_scale_exponent(
    h_days_array: np.ndarray, quantiles_h_array: np.ndarray, quantile_1d: float
) -> float:
    """
    Estimates the empirical Power Law Scale Exponent (1/xi) using a log-log regression.
    Equation IV.3.2.

    Parameters:
    h_days_array (np.ndarray): Array of risk horizons (e.g., [2, 5, 10, 20]).
    quantiles_h_array (np.ndarray): The measured empirical quantiles for each horizon.
    quantile_1d (float): The base 1-day empirical quantile.

    Returns:
    float: The estimated scale exponent (1/xi).
           (0.5 indicates Normal/Square-root scaling. >0.5 indicates trending/fat-tails).
    """
    # Calculate the Y-axis: ln(x_h) - ln(x_1)
    y_log_ratio = np.log(np.abs(quantiles_h_array)) - np.log(np.abs(quantile_1d))

    # Calculate the X-axis: ln(h)
    x_log_h = np.log(h_days_array)

    # We force the regression through the origin (no intercept) because when h=1, ln(h)=0 and ratio=0.
    model = sm.OLS(y_log_ratio, x_log_h)
    results = model.fit()

    # The slope is the scale exponent (1/xi)
    scale_exponent = results.params[0]

    return scale_exponent


def compute(data, quantiles_h=None, quantile_1d=None) -> dict:
    """Standard facade: empirical scale exponent as a JSON dict.

    Parameters:
    data: 1-D array-like of risk horizons in days (>= 2 horizons, all > 1).
    quantiles_h: 1-D array-like of measured quantiles per horizon.
    quantile_1d (float): base 1-day quantile (non-zero).

    Returns:
    dict: {"scale_exponent", "n_horizons"}; 0.5 indicates square-root-of-time
    (normal) scaling, > 0.5 indicates trending/fat tails.
    """
    if quantiles_h is None or quantile_1d is None:
        raise ValueError("quantiles_h and quantile_1d are required")
    h = np.asarray(data, dtype=float).ravel()
    q = np.asarray(quantiles_h, dtype=float).ravel()
    if h.shape != q.shape or h.size < 2:
        raise ValueError("horizons and quantiles must be equal-length arrays of size >= 2")
    if np.any(h <= 1.0):
        raise ValueError("all horizons must exceed 1 day")
    if float(quantile_1d) == 0.0:
        raise ValueError("quantile_1d must be non-zero")

    exponent = estimate_scale_exponent(h, q, float(quantile_1d))
    return {"scale_exponent": float(exponent), "n_horizons": int(h.size)}


if __name__ == "__main__":
    # --- Example IV.3.2.4: Scale Exponents for S&P 500 ---
    # Mock data representing empirical measurements of the 5% Quantile over various horizons
    h_horizons = np.array([2, 5, 10, 20])
    var_1d = 0.0150  # 1.50% Base 1-day VaR

    # Measured multi-day VaRs (simulated to reflect a scale exponent of approx ~0.45)
    vars_h = np.array([0.0205, 0.0310, 0.0425, 0.0580])

    empirical_exponent = estimate_scale_exponent(h_horizons, vars_h, var_1d)

    print(f"Empirical Scale Exponent (1/xi): {empirical_exponent:.4f}")
    if empirical_exponent < 0.5:
        print(
            "Interpretation: Risk scales slower than the square root of time (Mean-Reverting / Anti-persistent)."
        )
    elif empirical_exponent > 0.5:
        print(
            "Interpretation: Risk scales faster than the square root of time (Trending / Persistent)."
        )
