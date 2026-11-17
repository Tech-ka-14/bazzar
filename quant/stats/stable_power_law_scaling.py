"""Power-law scaling of historical VaR across horizons.

VaR_h = VaR_1 * h^c; c = 0.5 recovers the square-root-of-time rule (normal),
c > 0.5 reflects heavy-tailed/stable behaviour. Reference: Alexander (2008),
Vol. IV.
"""


def scale_historical_var(var_1_day: float, h_days: int, scale_exponent: float) -> float:
    """
    Scales a 1-day Historical VaR to an h-day VaR using a generalized power law.

    Parameters:
    var_1_day (float): The base 1-day VaR estimate.
    h_days (int): The target risk horizon in days.
    scale_exponent (float): The stability index/power scaling factor 'c'.
                            (0.5 = Normal/Square Root Rule. >0.5 = Heavy Tailed)
    """
    scaling_factor = h_days**scale_exponent
    return var_1_day * scaling_factor


def compute(data, h_days=None, scale_exponent=0.5) -> dict:
    """Standard facade: power-law horizon scaling of a 1-day VaR.

    Parameters:
    data (float): base 1-day VaR (positive, as a fraction).
    h_days (int): target horizon in days (>= 1).
    scale_exponent (float): stability index c (positive).

    Returns:
    dict: {"var_1_day", "horizon_days", "scale_exponent", "scaling_factor",
    "scaled_var"}.
    """
    var_1_day = float(data)
    if var_1_day <= 0.0:
        raise ValueError("1-day VaR must be positive")
    if h_days is None or int(h_days) < 1:
        raise ValueError("h_days must be a positive integer")
    if float(scale_exponent) <= 0.0:
        raise ValueError("scale_exponent must be positive")

    scaled = scale_historical_var(var_1_day, int(h_days), float(scale_exponent))
    return {
        "var_1_day": var_1_day,
        "horizon_days": int(h_days),
        "scale_exponent": float(scale_exponent),
        "scaling_factor": float(int(h_days) ** float(scale_exponent)),
        "scaled_var": float(scaled),
    }


if __name__ == "__main__":
    # --- Conceptual Demonstration ---
    base_1d_var = 0.015  # 1.5% 1-day VaR
    target_horizon = 10  # 10-day Risk Horizon

    # 1. Using the naive "Square Root of Time" Rule (c = 0.5)
    var_10d_naive = scale_historical_var(base_1d_var, target_horizon, scale_exponent=0.5)

    # 2. Using a customized Power Law for a heavy-tailed stable distribution (e.g., c = 0.6)
    var_10d_heavy = scale_historical_var(base_1d_var, target_horizon, scale_exponent=0.6)

    print(f"Base 1-Day VaR: {base_1d_var:.2%}")
    print(f"10-Day VaR (Naive Square Root Rule): {var_10d_naive:.2%}")
    print(f"10-Day VaR (Empirical Power Law c=0.6): {var_10d_heavy:.2%}")
    print(
        f"Difference in risk estimate: {var_10d_heavy - var_10d_naive:.2%} (The naive rule severely understates the scaled risk)"
    )
