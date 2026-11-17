"""White's heteroscedasticity-consistent standard errors.

Robust covariance matrix T (X'X)^-1 Sigma (X'X)^-1 with
Sigma = (1/T) sum_t e_t^2 x_t x_t' for the OLS estimators.
"""

import numpy as np


def whites_robust_covariance(X, residuals):
    """
    Calculates White's Heteroscedasticity-Consistent Covariance Matrix.

    Parameters:
    X (numpy.ndarray): Explanatory variables matrix (T x k), including constant.
    residuals (numpy.ndarray): OLS residuals vector (T x 1).

    Returns:
    numpy.ndarray: White's robust covariance matrix for the estimated coefficients.
    """
    T, k = X.shape

    # Calculate (X'X)^-1
    XX_inv = np.linalg.inv(X.T @ X)

    # Calculate Sigma: the sum of e_t^2 * (x_t * x_t') divided by T
    Sigma = np.zeros((k, k))
    for t in range(T):
        x_t = X[t, :].reshape(-1, 1)  # Column vector for observation t
        e_t_sq = residuals[t] ** 2
        Sigma += e_t_sq * (x_t @ x_t.T)

    Sigma /= T

    # Calculate White's Robust Covariance Matrix: T * (X'X)^-1 * Sigma * (X'X)^-1
    robust_cov = T * (XX_inv @ Sigma @ XX_inv)

    return robust_cov


def compute(data, X=None) -> dict:
    """Standard facade: White's robust covariance and standard errors.

    Parameters:
    data: 1-D array-like of T OLS residuals.
    X: T x k design matrix (including a constant column).

    Returns:
    dict: {"robust_covariance", "robust_standard_errors"} with plain lists.
    """
    if X is None:
        raise ValueError("X is required")
    residuals = np.asarray(data, dtype=float).ravel()
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or X.shape[0] != residuals.size:
        raise ValueError("X must be a 2-D matrix with one row per residual")

    robust_cov = whites_robust_covariance(X, residuals)
    return {
        "robust_covariance": np.asarray(robust_cov, dtype=float).tolist(),
        "robust_standard_errors": np.sqrt(np.diag(robust_cov)).tolist(),
    }


if __name__ == "__main__":
    # Synthetic Data Setup
    np.random.seed(42)
    T = 100
    X = np.column_stack((np.ones(T), np.random.normal(0, 1, T)))
    residuals = np.random.normal(0, 1, T) * X[:, 1]  # Introduce heteroscedasticity

    robust_cov_matrix = whites_robust_covariance(X, residuals)
    robust_std_errors = np.sqrt(np.diag(robust_cov_matrix))

    print("White's Robust Standard Errors:")
    print(np.round(robust_std_errors, 4))
