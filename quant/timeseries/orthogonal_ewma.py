"""Orthogonal EWMA covariance construction.

P-EWMA: runs EWMA on the eigenvalues (principal-component variances) and
re-assembles the covariance matrix with the fixed eigenvector matrix,
guaranteeing positive definiteness and removing negative-correlation
artefacts of pairwise EWMA.
"""

import numpy as np


def orthogonal_ewma_covariance(returns_matrix, lam=0.94):
    """
    Computes the Orthogonal EWMA (P-EWMA) covariance matrix.

    returns_matrix: T x m matrix of asset returns.
    """
    T, m = returns_matrix.shape

    # 1. Perform PCA on the historical data to get eigenvalues and eigenvectors
    sample_cov = np.cov(returns_matrix, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(sample_cov)

    # Sort in descending order
    idx = np.argsort(eigenvalues)[::-1]
    W = eigenvectors[:, idx]

    # 2. Compute the principal components (P = X * W)
    principal_components = returns_matrix @ W

    # 3. Run standard EWMA on the variances of the principal components
    # Initialize variances with sample variances of the PCs
    pc_variances = np.var(principal_components, axis=0)

    for t in range(T):
        # Squared returns of PCs at time t
        pc_sq_returns = principal_components[t, :] ** 2
        pc_variances = lam * pc_variances + (1 - lam) * pc_sq_returns

    # 4. Reassemble the Covariance Matrix: V = W * Lambda * W'
    lambda_diag = np.diag(pc_variances)
    p_ewma_covariance = W @ lambda_diag @ W.T

    return p_ewma_covariance


def compute(returns_matrix, lam=0.94) -> dict:
    """Standard facade: P-EWMA covariance as a JSON-serializable dict.

    Parameters:
    returns_matrix: 2-D array-like (T observations x m assets) of returns.
    lam (float): EWMA decay factor in (0, 1).

    Returns:
    dict: {"n_observations", "n_assets", "lambda", "covariance"} with the
    P-EWMA covariance matrix as a nested list of plain floats.
    """
    returns_matrix = np.asarray(returns_matrix, dtype=float)
    if returns_matrix.ndim != 2 or min(returns_matrix.shape) < 2:
        raise ValueError("returns_matrix must be a 2-D array with at least 2 rows and columns")
    lam = float(lam)
    if not 0.0 < lam < 1.0:
        raise ValueError("lam must be in the open interval (0, 1)")

    covariance = orthogonal_ewma_covariance(returns_matrix, lam)
    return {
        "n_observations": int(returns_matrix.shape[0]),
        "n_assets": int(returns_matrix.shape[1]),
        "lambda": lam,
        "covariance": covariance.tolist(),
    }
