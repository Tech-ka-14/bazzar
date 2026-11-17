"""Rank-correlation calibration of elliptical copula parameters.

Maps an empirical Kendall's tau or Spearman's rho to the correlation
parameter rho of an elliptical (Normal or Student-t) copula via the
inversion formulas rho = sin(pi/2 * tau) (Eq. II.6.78) and
rho = 2 sin(pi/6 * rho_S) (Eq. II.6.79) of Alexander (2008), Vol. II.
"""

import numpy as np


def calibrate_elliptical_copula(rank_correlation_value, method="kendall"):
    """
    Calibrates the correlation parameter (rho) of an elliptical copula
    (Normal or Student-t) using empirical rank correlations.

    Parameters:
    rank_correlation_value: The estimated Kendall's tau or Spearman's rho from data.
    method: 'kendall' or 'spearman'
    """
    # Ensure the correlation value is within valid bounds [-1, 1]
    val = np.clip(rank_correlation_value, -1.0, 1.0)

    if method.lower() == "kendall":
        # Equation II.6.78
        copula_rho = np.sin((np.pi / 2.0) * val)

    elif method.lower() == "spearman":
        # Equation II.6.79
        copula_rho = 2.0 * np.sin((np.pi / 6.0) * val)

    else:
        raise ValueError("Method must be 'kendall' or 'spearman'")

    return copula_rho


def compute(rank_correlation_value: float, method: str = "kendall") -> dict:
    """Standard facade: elliptical copula calibration as a JSON dict.

    Returns:
    dict: {"method", "rank_correlation", "rho"} with plain floats.
    """
    rho = calibrate_elliptical_copula(float(rank_correlation_value), method=str(method))
    return {
        "method": str(method).lower(),
        "rank_correlation": float(rank_correlation_value),
        "rho": float(rho),
    }


if __name__ == "__main__":
    # Example Usage:
    # Assume we calculated a Kendall's Tau of 0.50 between two asset returns
    tau_empirical = 0.50
    estimated_rho = calibrate_elliptical_copula(tau_empirical, method="kendall")
    print(f"Calibrated Copula Parameter (Rho): {estimated_rho:.4f}")
