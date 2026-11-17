"""Normal scenario VaR and ETL, univariate and multivariate.

Scenario VaR/ETL under a normal distribution of uncertainty around the
expected change: VaR = Z sigma - mu, ETL = (phi(z_alpha)/alpha) sigma -
mu; the multivariate case maps exposures to a covariance matrix.
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.7.2.
"""

import numpy as np
import scipy.stats as stats


def normal_scenario_var_etl(mu: float, sigma: float, alpha: float) -> tuple:
    """
    Calculates univariate Scenario VaR and ETL assuming a normal distribution
    of uncertainty around the expected return.
    """
    z_score = stats.norm.ppf(1 - alpha)
    var = (z_score * sigma) - mu

    # Normal ETL analytical formula
    pdf_val = stats.norm.pdf(stats.norm.ppf(alpha))
    etl = (pdf_val / alpha) * sigma - mu
    return var, etl


def multivariate_scenario_var(
    exposures: np.ndarray, expected_changes: np.ndarray, covariance_matrix: np.ndarray, alpha: float
) -> float:
    """
    Calculates multivariate normal scenario VaR given an exposure vector (theta),
    expected changes (mu), and uncertainty covariance (Omega).
    """
    z_score = stats.norm.ppf(1 - alpha)

    # Portfolio variance: theta' * Omega * theta
    portfolio_variance = exposures.T @ covariance_matrix @ exposures
    portfolio_volatility = np.sqrt(portfolio_variance)

    # Expected portfolio change: theta' * mu
    expected_portfolio_change = exposures.T @ expected_changes

    var = (z_score * portfolio_volatility) - expected_portfolio_change
    return var


def compute(exposures, expected_changes, covariance_matrix, alpha: float = 0.01) -> dict:
    """Standard facade: multivariate normal scenario VaR as a JSON dict.

    Parameters:
    exposures: 1-D array-like of exposures to the scenario risk factors.
    expected_changes: 1-D array-like of expected factor changes.
    covariance_matrix: Square covariance matrix matching len(exposures).
    alpha (float): Tail probability in (0, 1), e.g. 0.01.

    Returns:
    dict: {"method", "alpha", "var"} with "var" the positive loss.
    """
    theta = np.asarray(exposures, dtype=float).ravel()
    mu = np.asarray(expected_changes, dtype=float).ravel()
    omega = np.asarray(covariance_matrix, dtype=float)
    if theta.size == 0:
        raise ValueError("exposures must contain at least one entry")
    if mu.size != theta.size:
        raise ValueError("expected_changes must have the same length as exposures")
    if omega.shape != (theta.size, theta.size):
        raise ValueError("covariance_matrix must be square with size len(exposures)")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    var = multivariate_scenario_var(theta, mu, omega, float(alpha))
    return {"method": "multivariate_normal_scenario", "alpha": float(alpha), "var": float(var)}
