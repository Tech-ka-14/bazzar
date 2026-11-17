"""Theoretical moments of a normal mixture distribution.

Non-central moments are probability-weighted averages of the component
moments; central moments, skewness and kurtosis follow Equations
IV.2.73-IV.2.74. Reference: Alexander (2008), Vol. IV, Example IV.2.21.
"""

import numpy as np


def calculate_mixture_moments(weights: np.ndarray, means: np.ndarray, vols: np.ndarray):
    """
    Calculates the theoretical moments (Mean, Variance, Skewness, Kurtosis)
    of a Normal Mixture Distribution (Equations IV.2.73 and IV.2.74).
    """
    # Equation IV.2.73: Non-Central Moments
    m1 = np.sum(weights * means)
    m2 = np.sum(weights * (vols**2 + means**2))
    m3 = np.sum(weights * (3 * means * vols**2 + means**3))
    m4 = np.sum(weights * (3 * vols**4 + 6 * means**2 * vols**2 + means**4))

    # Equation IV.2.74: Central Moments (Mean, Variance, Skewness, Kurtosis)
    mu = m1
    variance = m2 - m1**2
    sigma = np.sqrt(variance)

    skewness = (m3 - 3 * m1 * m2 + 2 * m1**3) / (sigma**3)
    kurtosis = (m4 - 4 * m1 * m3 + 6 * (m1**2) * m2 - 3 * m1**4) / (sigma**4)

    # Note: The result is raw kurtosis. Excess kurtosis is kurtosis - 3.
    return mu, sigma, skewness, kurtosis


def compute(data, means=None, vols=None) -> dict:
    """Standard facade: theoretical normal-mixture moments as a JSON dict.

    Parameters:
    data: 1-D array-like of component weights summing to 1.
    means: 1-D array-like of component means.
    vols: 1-D array-like of component volatilities (positive).

    Returns:
    dict: {"mean", "volatility", "skewness", "kurtosis", "excess_kurtosis"}.
    """
    if means is None or vols is None:
        raise ValueError("means and vols are required")
    weights = np.asarray(data, dtype=float).ravel()
    means = np.asarray(means, dtype=float).ravel()
    vols = np.asarray(vols, dtype=float).ravel()
    if not (weights.shape == means.shape == vols.shape):
        raise ValueError("weights, means and vols must have equal length")
    if weights.size < 2:
        raise ValueError("at least two mixture components are required")
    if not np.isclose(weights.sum(), 1.0):
        raise ValueError("weights must sum to 1")
    if np.any(vols <= 0.0):
        raise ValueError("vols must be positive")

    mu, sigma, skewness, kurtosis = calculate_mixture_moments(weights, means, vols)
    return {
        "mean": float(mu),
        "volatility": float(sigma),
        "skewness": float(skewness),
        "kurtosis": float(kurtosis),
        "excess_kurtosis": float(kurtosis - 3.0),
    }


if __name__ == "__main__":
    # Example IV.2.21: Parameters from Table IV.2.26 (Annualized)
    weights_annual = np.array([0.34003, 1 - 0.34003])
    means_annual = np.array([-0.3107, 0.2052])
    vols_annual = np.array([0.2649, 0.0952])

    mu, vol, skew, kurt = calculate_mixture_moments(weights_annual, means_annual, vols_annual)

    print("--- Theoretical Moments of the Normal Mixture ---")
    print(f"Mean: {mu:.4%}")
    print(f"Volatility: {vol:.4%}")
    print(f"Skewness: {skew:.4f}")
    print(f"Excess Kurtosis: {kurt - 3:.4f}")
