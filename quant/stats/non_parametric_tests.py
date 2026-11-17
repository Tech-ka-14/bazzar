"""Non-parametric goodness-of-fit statistics.

Kolmogorov-Smirnoff statistic sup|F1 - F2| and a tail-weighted
Anderson-Darling statistic sup |Fe - Fh| / sqrt(Fh (1 - Fh)).
"""

import numpy as np


def kolmogorov_smirnoff_statistic(f1_cdf_values, f2_cdf_values):
    """
    Calculates the KS test statistic: the maximum vertical difference
    between two cumulative distribution functions.
    """
    # Ensure inputs are numpy arrays
    f1 = np.array(f1_cdf_values)
    f2 = np.array(f2_cdf_values)

    ks_stat = np.max(np.abs(f1 - f2))
    return ks_stat


def anderson_darling_statistic(f_empirical_values, f_hypothesized_values):
    """
    Calculates the specific AD statistic defined in the text,
    designed to emphasize tail fit.
    """
    f_e = np.array(f_empirical_values)
    f_h = np.array(f_hypothesized_values)

    # Avoid division by zero at the extreme edges (where F(x) = 0 or 1)
    # by adding a tiny epsilon if necessary, though true CDFs evaluated
    # strictly strictly inside the bounds usually avoid this.
    epsilon = 1e-10
    f_h_clamped = np.clip(f_h, epsilon, 1 - epsilon)

    numerator = np.abs(f_e - f_h_clamped)
    denominator = np.sqrt(f_h_clamped * (1 - f_h_clamped))

    ad_stat = np.max(numerator / denominator)
    return ad_stat


def compute(data, f2_cdf_values=None, hypothesized_cdf_values=None) -> dict:
    """Standard facade: KS and Anderson-Darling statistics.

    Parameters:
    data: 1-D array-like of empirical CDF values F1 (or Fe).
    f2_cdf_values: optional second CDF sample for the KS statistic.
    hypothesized_cdf_values: optional hypothesized CDF for the
    Anderson-Darling statistic.

    Returns:
    dict: with "ks_statistic" and/or "anderson_darling_statistic".
    """
    f1 = np.asarray(data, dtype=float).ravel()
    if f1.size < 2:
        raise ValueError("data must contain at least 2 CDF values")

    out = {}
    if f2_cdf_values is not None:
        out["ks_statistic"] = float(
            kolmogorov_smirnoff_statistic(f1, np.asarray(f2_cdf_values, dtype=float))
        )
    if hypothesized_cdf_values is not None:
        out["anderson_darling_statistic"] = float(
            anderson_darling_statistic(f1, np.asarray(hypothesized_cdf_values, dtype=float))
        )
    if not out:
        raise ValueError("provide f2_cdf_values and/or hypothesized_cdf_values")
    return out
