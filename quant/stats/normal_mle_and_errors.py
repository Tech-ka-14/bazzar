"""Maximum likelihood estimation for the normal distribution.

MLEs of the mean and variance (the variance MLE divides by n, not n - 1)
with standard errors from the diagonal of the inverse information matrix.
Reference: Alexander (2008), Vol. I.
"""

import numpy as np


def normal_mle_parameters(data):
    """
    Calculates the Maximum Likelihood Estimators for a normal distribution.
    Note: The MLE for variance divides by n, not n-1.
    """
    n = len(data)
    mle_mean = np.sum(data) / n
    # Alternatively: mle_mean = np.mean(data)

    mle_variance = np.sum((data - mle_mean) ** 2) / n
    # Alternatively: mle_variance = np.var(data, ddof=0)

    return mle_mean, mle_variance


def normal_mle_standard_errors(mle_variance, n):
    """
    Calculates the standard errors of the MLE estimates for a normal distribution
    using the diagonal elements of the inverse Information Matrix.
    """
    mle_std = np.sqrt(mle_variance)

    # Standard error of the mean: sigma / sqrt(n)
    se_mean = mle_std / np.sqrt(n)

    # Standard error of the variance: sigma^2 / sqrt(2n)
    se_variance = mle_variance / np.sqrt(2 * n)

    return se_mean, se_variance


def compute(data) -> dict:
    """Standard facade: normal MLE estimates and standard errors.

    Parameters:
    data: 1-D array-like of observations (at least 2).

    Returns:
    dict: {"n", "mle_mean", "mle_variance", "se_mean", "se_variance"}.
    """
    arr = np.asarray(data, dtype=float).ravel()
    if arr.size < 2:
        raise ValueError("data must contain at least 2 observations")

    mean_est, var_est = normal_mle_parameters(arr)
    se_mean, se_variance = normal_mle_standard_errors(var_est, arr.size)
    return {
        "n": int(arr.size),
        "mle_mean": float(mean_est),
        "mle_variance": float(var_est),
        "se_mean": float(se_mean),
        "se_variance": float(se_variance),
    }


if __name__ == "__main__":
    # Example Usage
    sample_data = np.array([0.01, -0.02, 0.015, 0.005, -0.01])
    n_obs = len(sample_data)

    mean_est, var_est = normal_mle_parameters(sample_data)
    se_mu, se_var = normal_mle_standard_errors(var_est, n_obs)

    print(f"MLE Mean: {mean_est:.4f} (SE: {se_mu:.4f})")
    print(f"MLE Variance: {var_est:.6f} (SE: {se_var:.6f})")
