"""EWMA covariance matrix forecasting.

Recursively updates the multivariate covariance matrix with the outer
product of the latest returns vector; the most recent state is the
quadratically weighted EWMA covariance forecast.
"""

import numpy as np


def calculate_ewma_covariance(returns_matrix, lam=0.94):
    """
    Computes the EWMA Covariance matrix for a matrix of asset returns.

    returns_matrix: A T x m numpy array of returns (T observations, m assets).
    lam: The decay factor (e.g., 0.94 for daily data, 0.97 for monthly).
    """
    # 1. Extract dimensions
    T, m = returns_matrix.shape

    # 2. Initialize the covariance matrix using the sample covariance
    current_covariance = np.cov(returns_matrix, rowvar=False)

    # 3. Iterate through time to update the EWMA Covariance recursively
    for t in range(T):
        # Extract the return vector for time t (m x 1)
        returns_vector = returns_matrix[t, :].reshape(m, 1)

        # Calculate the outer product of the return vector: x * x'
        outer_product = returns_vector @ returns_vector.T

        # Update the covariance matrix
        current_covariance = lam * current_covariance + (1 - lam) * outer_product

    return current_covariance


def compute(returns_matrix, lam=0.94) -> dict:
    """Standard facade: EWMA covariance forecast as a JSON-serializable dict.

    Parameters:
    returns_matrix: 2-D array-like (T observations x m assets) of returns.
    lam (float): EWMA decay factor in (0, 1), e.g. 0.94 for daily data.

    Returns:
    dict: {"n_observations", "n_assets", "lambda", "covariance"} with the
    EWMA covariance matrix as a nested list of plain floats.
    """
    returns_matrix = np.asarray(returns_matrix, dtype=float)
    if returns_matrix.ndim != 2 or min(returns_matrix.shape) < 2:
        raise ValueError("returns_matrix must be a 2-D array with at least 2 rows and columns")
    lam = float(lam)
    if not 0.0 < lam < 1.0:
        raise ValueError("lam must be in the open interval (0, 1)")

    covariance = calculate_ewma_covariance(returns_matrix, lam)
    return {
        "n_observations": int(returns_matrix.shape[0]),
        "n_assets": int(returns_matrix.shape[1]),
        "lambda": lam,
        "covariance": covariance.tolist(),
    }
