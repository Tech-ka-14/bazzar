"""Systematic normal linear VaR via matrix algebra.

VaR = Z * sqrt(theta' Omega theta), optionally drift-adjusted by the
expected excess return theta' mu.
Reference: Alexander (2008), Market Risk Analysis IV, Equations
IV.2.14-IV.2.15.
"""

import numpy as np
from scipy.stats import norm


def calculate_systematic_var(
    theta: np.ndarray, omega_h: np.ndarray, mu_h: np.ndarray = None, alpha: float = 0.01
) -> float:
    """
    Calculates the Systematic Normal Linear VaR using matrix algebra.

    Parameters:
    theta (np.ndarray): The risk factor sensitivity vector (m x 1).
    omega_h (np.ndarray): The h-day covariance matrix of risk factor returns (m x m).
    mu_h (np.ndarray, optional): The vector of expected excess returns (m x 1). Defaults to zero drift.
    alpha (float): The significance level (e.g., 0.01 for 99% confidence).

    Returns:
    float: The Systematic VaR.
    """
    # Calculate portfolio variance: theta' * Omega * theta
    variance = theta.T @ omega_h @ theta
    volatility = np.sqrt(variance)

    # Standard normal critical value
    critical_value = norm.ppf(1 - alpha)

    # Calculate base VaR
    var_base = critical_value * volatility

    # Apply drift adjustment if mu_h is provided (Eq. IV.2.14)
    if mu_h is not None:
        expected_return = theta.T @ mu_h
        return var_base - expected_return

    # Return zero-drift VaR (Eq. IV.2.15)
    return var_base


# Example Usage


def compute(theta, omega_h, mu_h=None, alpha: float = 0.01) -> dict:
    """Standard facade: systematic normal linear VaR as a JSON dict.

    Parameters:
    theta: 1-D array-like of risk factor sensitivities.
    omega_h: Square h-day covariance matrix matching len(theta).
    mu_h: Optional 1-D array-like of expected excess returns.
    alpha (float): Tail probability in (0, 1), e.g. 0.01.

    Returns:
    dict: {"method", "alpha", "var"} with "var" the positive loss.
    """
    theta = np.asarray(theta, dtype=float).ravel()
    omega = np.asarray(omega_h, dtype=float)
    if theta.size == 0:
        raise ValueError("theta must contain at least one sensitivity")
    if omega.shape != (theta.size, theta.size):
        raise ValueError("omega_h must be square with size len(theta)")
    if mu_h is not None:
        mu_h = np.asarray(mu_h, dtype=float).ravel()
        if mu_h.size != theta.size:
            raise ValueError("mu_h must have the same length as theta")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    var = calculate_systematic_var(theta, omega, mu_h, float(alpha))
    return {
        "method": "systematic_normal_linear",
        "alpha": float(alpha),
        "var": float(var),
    }


if __name__ == "__main__":
    theta_vec = np.array([0.5, 0.3, 0.2])  # Sensitivities to 3 factors
    omega_mat = np.array(
        [[0.0004, 0.0001, 0.00005], [0.0001, 0.0009, 0.0002], [0.00005, 0.0002, 0.0016]]
    )

    sys_var = calculate_systematic_var(theta_vec, omega_mat, alpha=0.01)
    print(f"1% Systematic VaR (Zero Drift): {sys_var:.4%}")
