"""Orthogonal (PCA) regression.

Regresses y on the principal components of X and rotates the estimates back
to the original coordinates, stabilizing estimation under multicollinearity.
Reference: Alexander (2008), Vol. I.
"""

import numpy as np


def orthogonal_regression(X, y):
    """
    Performs Orthogonal Regression using Principal Component Analysis (PCA).

    Parameters:
    X (numpy.ndarray): Explanatory variables matrix (T x k), WITHOUT the constant term.
    y (numpy.ndarray): Dependent variable vector (T x 1).

    Returns:
    dict: A dictionary containing PCA estimators, recovered original estimators,
          and their respective covariance matrices.
    """
    T, k = X.shape

    # 1. Standardize X and perform PCA to get Eigenvectors (W) and Principal Components (P_raw)
    # Note: In practice, variables are centered before PCA.
    X_centered = X - np.mean(X, axis=0)
    cov_matrix = np.cov(X_centered, rowvar=False)

    # Calculate eigenvalues and eigenvectors
    eigenvalues, W = np.linalg.eigh(cov_matrix)

    # Sort eigenvalues and eigenvectors in descending order
    idx = np.argsort(eigenvalues)[::-1]
    W = W[:, idx]

    # Compute the principal components (Scores)
    P_raw = X_centered @ W

    # 2. Append a column of 1s to P for the constant term
    ones = np.ones((T, 1))
    P = np.hstack((ones, P_raw))

    # 3. Calculate PCA OLS Estimators (beta_hat_PCA)
    P_prime_P_inv = np.linalg.inv(P.T @ P)
    beta_hat_PCA = P_prime_P_inv @ (P.T @ y)

    # Calculate Residuals and Standard Error of the Regression (s^2)
    y_hat = P @ beta_hat_PCA
    residuals = y - y_hat
    RSS = residuals.T @ residuals
    s_squared = RSS / (T - k - 1)  # T - k - 1 degrees of freedom

    # Covariance Matrix of PCA estimators
    cov_beta_PCA = s_squared * P_prime_P_inv

    # 4. Construct the Augmented Eigenvector Matrix (W_tilde)
    W_tilde = np.zeros((k + 1, k + 1))
    W_tilde[0, 0] = 1.0
    W_tilde[1:, 1:] = W

    # 5. Recover the Original Estimated Coefficients (beta_hat)
    beta_hat = W_tilde @ beta_hat_PCA

    # 6. Recover the Original Covariance Matrix
    cov_beta_original = s_squared * (W_tilde @ P_prime_P_inv @ W_tilde.T)

    return {
        "beta_hat_PCA": beta_hat_PCA.flatten(),
        "cov_beta_PCA": cov_beta_PCA,
        "beta_hat_original": beta_hat.flatten(),
        "cov_beta_original": cov_beta_original,
        "s_squared": s_squared,
        "W_tilde": W_tilde,
    }


def compute(data, X=None) -> dict:
    """Standard facade: orthogonal (PCA) regression as a JSON dict.

    Parameters:
    data: 1-D array-like of T dependent-variable observations.
    X: T x k explanatory matrix (without a constant column); k >= 2 is
    required for the PCA rotation.

    Returns:
    dict: {"coefficients", "pca_coefficients", "standard_errors",
    "s_squared"}; coefficients are in the original coordinates with the
    intercept first.
    """
    if X is None:
        raise ValueError("X is required")
    y = np.asarray(data, dtype=float).ravel()
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or X.shape[0] != y.size:
        raise ValueError("X must be a 2-D matrix with one row per observation")
    if X.shape[1] < 2:
        raise ValueError("at least 2 explanatory variables are required")
    if X.shape[0] <= X.shape[1] + 1:
        raise ValueError("more observations than parameters are required")

    results = orthogonal_regression(X, y)
    return {
        "coefficients": np.asarray(results["beta_hat_original"], dtype=float).tolist(),
        "pca_coefficients": np.asarray(results["beta_hat_PCA"], dtype=float).tolist(),
        "standard_errors": np.sqrt(np.diag(results["cov_beta_original"])).tolist(),
        "s_squared": float(results["s_squared"]),
    }


if __name__ == "__main__":
    # --- Synthetic Example (Replicating the Billiton/Oil/Gold Concept) ---
    # T = 100 observations, k = 2 highly correlated explanatory variables
    np.random.seed(42)
    T = 100

    # Create two highly collinear variables (e.g., Oil and Gold proxy)
    X1 = np.random.normal(0, 0.02, T)
    X2 = X1 + np.random.normal(0, 0.005, T)  # X2 is highly correlated with X1
    X = np.column_stack((X1, X2))

    # Generate dependent variable y with some noise
    y = 0.0025 + 0.3 * X1 + 0.5 * X2 + np.random.normal(0, 0.01, T)

    # Run Orthogonal Regression
    results = orthogonal_regression(X, y)

    print("--- Orthogonal Regression Results ---")
    print("\n1. PCA Coefficients (beta_hat_PCA):")
    print(np.round(results["beta_hat_PCA"], 4))

    print("\n2. Recovered Original Coefficients (beta_hat):")
    print(f"Constant: {results['beta_hat_original'][0]:.4f}")
    print(f"Variable 1: {results['beta_hat_original'][1]:.4f}")
    print(f"Variable 2: {results['beta_hat_original'][2]:.4f}")

    print("\n3. Diagonal of Original Covariance Matrix (Variances):")
    print(np.round(np.diag(results["cov_beta_original"]), 6))
