"""Likelihood-ratio backtest of a distribution forecast.

Tests whether the transformed probability series Z_ht (probability
integral transform of realized returns under the forecast distribution)
follows a standard normal, using a chi-squared(2) likelihood-ratio
statistic.
Reference: Alexander (2008), Market Risk Analysis IV, Equation IV.6.42.
"""

import numpy as np
import scipy.stats as stats


def distribution_likelihood_ratio_test(z_series: np.ndarray) -> tuple:
    """
    Performs a Likelihood Ratio test to check if the transformed probabilities
    Z_ht follow a Standard Normal N(0,1) distribution.
    """
    T = len(z_series)
    mu_hat = np.mean(z_series)
    sigma_hat = np.std(z_series, ddof=0)

    # Calculate the test statistic (Eq IV.6.42)
    sum_z_squared = np.sum(z_series**2)
    sum_standardized_squared = np.sum(((z_series - mu_hat) / sigma_hat) ** 2)

    lr_statistic = sum_z_squared - sum_standardized_squared - (T * np.log(sigma_hat**2))

    # Distributed as Chi-Squared with 2 degrees of freedom
    p_value = 1 - stats.chi2.cdf(lr_statistic, df=2)

    return lr_statistic, p_value


def compute(z_series) -> dict:
    """Standard facade: distribution-forecast LR backtest as a JSON dict.

    Parameters:
    z_series: 1-D array-like of transformed probability realizations
    (should be N(0, 1) under a correct forecast distribution).

    Returns:
    dict: {"method", "n", "lr_statistic", "p_value"}.
    """
    z = np.asarray(z_series, dtype=float).ravel()
    if z.size < 2:
        raise ValueError("z_series must contain at least two observations")

    lr_stat, p_value = distribution_likelihood_ratio_test(z)
    return {
        "method": "distribution_lr_test",
        "n": int(z.size),
        "lr_statistic": float(lr_stat),
        "p_value": float(p_value),
    }
