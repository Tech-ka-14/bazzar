"""Precision of variance and volatility estimates.

Chi-squared confidence intervals for equally weighted variance and
volatility estimates with standard errors sqrt(2/T) and sqrt(1/(2T))
respectively. Reference: Alexander (2008), Vol. II.
"""

import numpy as np
import scipy.stats as stats


def variance_volatility_metrics(variance_estimate, T, confidence_level=0.95):
    """
    Calculates confidence intervals and standard errors for
    equally weighted variance and volatility estimates.
    """
    alpha = 1 - confidence_level

    # 1. Confidence Interval for Variance
    # Obtain the critical chi-squared values
    chi2_lower = stats.chi2.ppf(alpha / 2, T)
    chi2_upper = stats.chi2.ppf(1 - alpha / 2, T)

    # Calculate bounds
    var_lower_bound = (T * variance_estimate) / chi2_upper
    var_upper_bound = (T * variance_estimate) / chi2_lower

    # 2. Confidence Interval for Volatility (Square Root Transformation)
    volatility_estimate = np.sqrt(variance_estimate)
    vol_lower_bound = np.sqrt(var_lower_bound)
    vol_upper_bound = np.sqrt(var_upper_bound)

    # 3. Standard Errors
    # Percentage standard error for variance = sqrt(2/T)
    var_pct_se = np.sqrt(2 / T)
    var_se = var_pct_se * variance_estimate

    # Percentage standard error for volatility approx = sqrt(1 / (2T))
    vol_pct_se = np.sqrt(1 / (2 * T))
    vol_se = vol_pct_se * volatility_estimate

    return {
        "Variance Estimate": variance_estimate,
        "Variance CI": (var_lower_bound, var_upper_bound),
        "Variance Std Error": var_se,
        "Volatility Estimate": volatility_estimate,
        "Volatility CI": (vol_lower_bound, vol_upper_bound),
        "Volatility Std Error": vol_se,
    }


def compute(data, T=None, confidence_level=0.95) -> dict:
    """Standard facade: precision metrics for a variance estimate.

    Parameters:
    data (float): equally weighted variance estimate (positive).
    T (int): sample size used for the estimate (>= 2).
    confidence_level (float): confidence level in (0, 1).

    Returns:
    dict: {"variance", "variance_ci", "variance_std_error", "volatility",
    "volatility_ci", "volatility_std_error"}.
    """
    variance_estimate = float(data)
    if variance_estimate <= 0.0:
        raise ValueError("variance estimate must be positive")
    if T is None or int(T) < 2:
        raise ValueError("T must be at least 2")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be in the open interval (0, 1)")

    metrics = variance_volatility_metrics(variance_estimate, int(T), float(confidence_level))
    return {
        "variance": float(metrics["Variance Estimate"]),
        "variance_ci": [float(v) for v in metrics["Variance CI"]],
        "variance_std_error": float(metrics["Variance Std Error"]),
        "volatility": float(metrics["Volatility Estimate"]),
        "volatility_ci": [float(v) for v in metrics["Volatility CI"]],
        "volatility_std_error": float(metrics["Volatility Std Error"]),
    }


if __name__ == "__main__":
    # Example implementation based on text parameters
    metrics = variance_volatility_metrics(variance_estimate=0.04, T=30, confidence_level=0.95)
