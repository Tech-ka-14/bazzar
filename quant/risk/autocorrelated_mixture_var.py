"""Autocorrelation-adjusted time horizon for mixture VaR scaling.

For AR(1) autocorrelated returns the effective risk horizon is
h_tilde = h + 2 rho (1 - rho)^-2 [(h - 1)(1 - rho) - rho (1 - rho^(h-1))],
used in place of h when scaling mixture VaR.
Reference: Alexander (2008), Market Risk Analysis IV, Example IV.2.23.
"""

import numpy as np


def calculate_adjusted_time_horizon(h: int, rho: float) -> float:
    """Calculates adjusted time horizon (h_tilde) for AR1 process."""
    if rho == 0:
        return float(h)
    term_1 = (h - 1) * (1 - rho)
    term_2 = rho * (1 - rho ** (h - 1))
    return h + 2 * (rho / (1 - rho) ** 2) * (term_1 - term_2)


# Example IV.2.23: Mixture VaR with Autocorrelation


def compute(h: int, rho: float) -> dict:
    """Standard facade: autocorrelation-adjusted horizon as a JSON dict.

    Parameters:
    h (int): Risk horizon in days (>= 1).
    rho (float): First-order autocorrelation in (-1, 1).

    Returns:
    dict: {"method", "h", "rho", "adjusted_horizon"}.
    """
    h = int(h)
    rho = float(rho)
    if h < 1:
        raise ValueError("h must be a positive integer")
    if not -1.0 < rho < 1.0:
        raise ValueError("rho must be in the open interval (-1, 1)")

    h_tilde = calculate_adjusted_time_horizon(h, rho)
    return {
        "method": "autocorrelated_horizon",
        "h": h,
        "rho": rho,
        "adjusted_horizon": float(h_tilde),
    }


if __name__ == "__main__":
    h_days = 10
    rho_positive = 0.25
    rho_negative = -0.25

    h_tilde_pos = calculate_adjusted_time_horizon(h_days, rho_positive)
    h_tilde_neg = calculate_adjusted_time_horizon(h_days, rho_negative)

    print(f"Standard Time Horizon (h): {h_days}")
    print(f"Adjusted Horizon (Autocorrelation = +0.25): {h_tilde_pos:.2f}")
    print(f"Adjusted Horizon (Autocorrelation = -0.25): {h_tilde_neg:.2f}\n")

    print(
        f"If calculating 10-day Mixture VaR with +0.25 autocorrelation, scale daily volatilities by sqrt({h_tilde_pos:.2f}) (approx {np.sqrt(h_tilde_pos):.2f}) instead of sqrt({h_days})."
    )
