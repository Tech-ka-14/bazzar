"""Two-asset portfolio variance and minimum-variance weight.

Portfolio variance: w^2 sigma_1^2 + (1-w)^2 sigma_2^2 +
2 rho w (1-w) sigma_1 sigma_2. The minimum-variance weight on asset 1 is
w* = (sigma_2^2 - rho sigma_1 sigma_2) / (sigma_1^2 + sigma_2^2 -
2 rho sigma_1 sigma_2) (Example I.6.5, Alexander 2008).
"""

import numpy as np


def portfolio_variance_2_assets(w, vol1, vol2, rho):
    """
    Calculates the variance of a 2-asset portfolio.
    """
    variance = (w**2 * vol1**2) + ((1 - w) ** 2 * vol2**2) + (2 * rho * w * (1 - w) * vol1 * vol2)
    return variance


def min_variance_weight_2_assets(vol1, vol2, rho):
    """
    Calculates the optimal weight (w*) for Asset 1 that minimizes portfolio variance.
    """
    numerator = vol2**2 - (rho * vol1 * vol2)
    denominator = vol1**2 + vol2**2 - (2 * rho * vol1 * vol2)

    # Handle the edge case of perfectly correlated identical assets
    if denominator == 0:
        return 0.5

    return numerator / denominator


def compute(vol1: float, vol2: float, rho: float, w: float = None) -> dict:
    """Standard facade: two-asset minimum-variance portfolio as a JSON dict.

    Parameters:
    vol1 (float): Volatility of asset 1, positive.
    vol2 (float): Volatility of asset 2, positive.
    rho (float): Return correlation in [-1, 1].
    w (float, optional): Weight on asset 1 at which the portfolio variance
    is also reported.

    Returns:
    dict: {"min_variance_weight", "min_variance", "min_volatility",
    "weight", "variance_at_weight"}; the last two are None unless w is
    supplied.
    """
    vol1 = float(vol1)
    vol2 = float(vol2)
    rho = float(rho)
    if vol1 <= 0.0 or vol2 <= 0.0:
        raise ValueError("vol1 and vol2 must be positive")
    if not -1.0 <= rho <= 1.0:
        raise ValueError("rho must be in [-1, 1]")

    opt_w = min_variance_weight_2_assets(vol1, vol2, rho)
    min_var = portfolio_variance_2_assets(opt_w, vol1, vol2, rho)
    variance_at_w = None
    if w is not None:
        variance_at_w = float(portfolio_variance_2_assets(float(w), vol1, vol2, rho))
    return {
        "min_variance_weight": float(opt_w),
        "min_variance": float(min_var),
        "min_volatility": float(np.sqrt(min_var)),
        "weight": None if w is None else float(w),
        "variance_at_weight": variance_at_w,
    }


if __name__ == "__main__":
    # --- Example I.6.5 Implementation ---
    v1 = 0.20  # Asset 1 Volatility = 20%
    v2 = 0.30  # Asset 2 Volatility = 30%
    correlation = -0.25

    # Calculate Optimal Weight
    opt_w1 = min_variance_weight_2_assets(v1, v2, correlation)
    opt_w2 = 1 - opt_w1

    # Calculate Minimum Volatility
    min_var = portfolio_variance_2_assets(opt_w1, v1, v2, correlation)
    min_vol = np.sqrt(min_var)

    print("--- 2-Asset Minimum Variance Portfolio ---")
    print(f"Optimal Weight Asset 1: {opt_w1 * 100:.2f}%")
    print(f"Optimal Weight Asset 2: {opt_w2 * 100:.2f}%")
    print(f"Minimum Portfolio Volatility: {min_vol * 100:.2f}%")
