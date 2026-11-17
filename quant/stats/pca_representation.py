"""PCA representation of the original variables.

Approximates standardized variables from a truncated set of principal
components: X_approx = P_k W_k' (Equation II.2.6). Reference: Alexander
(2008), Vol. II.
"""

import numpy as np


def reconstruct_from_pca(principal_components, eigenvectors, num_components):
    """
    Approximates the original standardized variables (e.g., interest rate changes)
    using a truncated set of principal components.

    Parameters:
    principal_components (numpy.ndarray): T x n matrix of all principal component scores.
    eigenvectors (numpy.ndarray): n x n matrix of eigenvectors (factor weights).
    num_components (int): The number of components to keep (k).

    Returns:
    numpy.ndarray: T x n matrix of the approximated original variables.
    """
    # Truncate the components and the eigenvectors to the first 'k' dimensions
    p_k = principal_components[:, :num_components]
    w_k = eigenvectors[:, :num_components]

    # Reconstruct the original variables: X_approx = P_k * W_k^T
    # Note: Since the text defines it as weights * components for a single row,
    # the matrix equivalent for the full dataset is P_k @ W_k.T
    approximated_variables = p_k @ w_k.T

    return approximated_variables


def compute(data, eigenvectors=None, num_components=None) -> dict:
    """Standard facade: reconstruct variables from principal components.

    Parameters:
    data: T x n matrix of principal component scores.
    eigenvectors: n x n matrix of eigenvectors (factor weights) as columns.
    num_components (int): number of leading components to keep (k).

    Returns:
    dict: {"n_components", "reconstructed"} where reconstructed is the
    T x n matrix of approximated original variables.
    """
    if eigenvectors is None or num_components is None:
        raise ValueError("eigenvectors and num_components are required")
    P = np.asarray(data, dtype=float)
    W = np.asarray(eigenvectors, dtype=float)
    if P.ndim != 2 or W.ndim != 2 or W.shape[0] != W.shape[1] or W.shape[0] != P.shape[1]:
        raise ValueError("data must be T x n and eigenvectors n x n")
    k = int(num_components)
    if not 1 <= k <= P.shape[1]:
        raise ValueError("num_components must be between 1 and n")

    approximated = reconstruct_from_pca(P, W, k)
    return {
        "n_components": k,
        "reconstructed": np.asarray(approximated, dtype=float).tolist(),
    }


if __name__ == "__main__":
    # --- Example Application (Replicating Eq II.2.6 structure) ---
    T = 5  # 5 days of data
    n = 50  # 50 yield curve rates
    k = 3  # Keeping only Shift, Tilt, and Convexity components

    # Synthetic principal component scores (T x k)
    p_k_simulated = np.random.normal(0, 1, (T, k))

    # Synthetic first 3 eigenvectors for 50 rates (n x k)
    w_k_simulated = np.random.uniform(-0.2, 0.7, (n, k))

    # Reconstruct the 50 rates over 5 days using only the 3 components
    reconstructed_rates = p_k_simulated @ w_k_simulated.T

    print("--- PCA Dimensionality Reduction ---")
    print(f"Original shape required: {T} days x {n} rates")
    print(f"Approximated using: {T} days of {k} components")
    print(f"Shape of reconstructed data: {reconstructed_rates.shape}")
