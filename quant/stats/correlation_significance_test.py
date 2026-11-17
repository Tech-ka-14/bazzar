"""Significance test for a correlation estimate.

One-sided t-test of H0: rho <= 0 with statistic
t = rho_hat * sqrt(T) / sqrt(1 - rho_hat^2). Reference: Alexander (2008),
Vol. II, Example II.3.11.
"""

import numpy as np
import scipy.stats as stats


def test_correlation_significance(rho_hat, T, alpha=0.05):
    """
    Tests whether a historical correlation estimate is significantly greater than 0.
    """
    # Calculate the t-statistic
    t_stat = (rho_hat * np.sqrt(T)) / np.sqrt(1 - rho_hat**2)

    # Calculate the critical t-value and p-value for a one-sided test
    t_critical = stats.t.ppf(1 - alpha, T)
    p_value = stats.t.sf(t_stat, T)

    reject_null = t_stat > t_critical

    return {
        "Correlation Estimate": rho_hat,
        "Observations (T)": T,
        "t-statistic": t_stat,
        "Critical t-value": t_critical,
        "p-value": p_value,
        "Significant (Reject H0)": reject_null,
    }


def compute(rho_hat, T, alpha=0.05) -> dict:
    """Standard facade: correlation significance test as a JSON dict.

    Parameters:
    rho_hat (float): estimated correlation in (-1, 1).
    T (int): number of observations.
    alpha (float): significance level in (0, 1).

    Returns:
    dict: {"rho", "T", "t_statistic", "t_critical", "p_value",
    "significant"}.
    """
    rho_hat = float(rho_hat)
    if not -1.0 < rho_hat < 1.0:
        raise ValueError("rho_hat must be in the open interval (-1, 1)")
    if int(T) < 2:
        raise ValueError("T must be at least 2")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    result = test_correlation_significance(rho_hat, int(T), float(alpha))
    return {
        "rho": float(result["Correlation Estimate"]),
        "T": int(result["Observations (T)"]),
        "t_statistic": float(result["t-statistic"]),
        "t_critical": float(result["Critical t-value"]),
        "p_value": float(result["p-value"]),
        "significant": bool(result["Significant (Reject H0)"]),
    }


if __name__ == "__main__":
    # Example implementation based on Example II.3.11
    test_result = test_correlation_significance(rho_hat=0.2, T=36, alpha=0.10)
