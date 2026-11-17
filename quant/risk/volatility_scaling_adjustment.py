"""Autocorrelation-adjusted volatility scaling.

Scales daily volatility to an h-period horizon adjusting for first-order
autocorrelation: sigma_h = sigma_1 * sqrt(h + 2 rho/(1-rho) * (h - (1 -
rho^h)/(1 - rho))).
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.1.5.
"""

import numpy as np


def adjusted_volatility_scaling(daily_vol, h, rho):
    """
    Adjusts the volatility forecast for an h-period horizon when returns
    exhibit first-order autocorrelation (rho).

    Parameters:
    daily_vol (float): Daily volatility (sigma_1).
    h (int): Number of periods to forecast (e.g., 5 days, 22 days).
    rho (float): First-order autocorrelation coefficient.

    Returns:
    float: The adjusted h-period volatility.
    """
    # The variance scaling factor (h + 2 * sum(1 - j/h) * rho^j)
    # Simplified for first-order autocorrelation:
    # Var_h = Var_1 * [ h + 2 * rho * (h - (1 - rho^h)/(1 - rho)) / (1 - rho) ]

    # Calculate the variance multiplier (the term inside the square root)
    if rho == 0:
        multiplier = h
    else:
        # Summation formula for first-order autocorrelation
        multiplier = h + (2 * rho / (1 - rho)) * (h - (1 - rho**h) / (1 - rho))

    adjusted_vol = daily_vol * np.sqrt(multiplier)
    return adjusted_vol


def compute(daily_vol: float, h: int, rho: float = 0.0) -> dict:
    """Standard facade: autocorrelation-adjusted h-period volatility.

    Parameters:
    daily_vol (float): Daily volatility (positive).
    h (int): Forecast horizon in periods (>= 1).
    rho (float): First-order autocorrelation in (-1, 1).

    Returns:
    dict: {"method", "h", "rho", "volatility_standard",
    "volatility_adjusted"}.
    """
    if daily_vol <= 0:
        raise ValueError("daily_vol must be positive")
    if int(h) < 1:
        raise ValueError("h must be a positive integer")
    if not -1.0 < rho < 1.0:
        raise ValueError("rho must be in the open interval (-1, 1)")

    adjusted = adjusted_volatility_scaling(float(daily_vol), int(h), float(rho))
    standard = float(daily_vol) * np.sqrt(int(h))
    return {
        "method": "autocorrelated_vol_scaling",
        "h": int(h),
        "rho": float(rho),
        "volatility_standard": float(standard),
        "volatility_adjusted": float(adjusted),
    }


if __name__ == "__main__":
    # --- Example Application ---
    # Daily vol 1.5%, 10-day forecast, 10% positive serial correlation
    sigma_1 = 0.015
    h_days = 10
    rho_1 = 0.10

    # Standard Square-Root-of-Time
    standard_vol = sigma_1 * np.sqrt(h_days)

    # Adjusted
    adj_vol = adjusted_volatility_scaling(sigma_1, h_days, rho_1)

    print("--- Volatility Scaling Adjustment ---")
    print(f"Standard Forecast (i.i.d.): {standard_vol * 100:.2f}%")
    print(f"Adjusted Forecast (Autocorrelated): {adj_vol * 100:.2f}%")
