import numpy as np


def calculate_principal_component_representation(covariance_matrix, data_matrix):
    """
    Decomposes a covariance matrix into its principal components and
    calculates the PC representation of the data.

    Parameters:
    covariance_matrix (numpy.ndarray): The (n x n) covariance matrix of the system.
    data_matrix (numpy.ndarray): The (T x n) matrix of mean-deviated (centered) data.

    Returns:
    tuple: (eigenvalues, eigenvectors, principal_components)
    """
    # 1. Perform Eigen-decomposition
    # For symmetric matrices (like covariance matrices), np.linalg.eigh is faster and more stable
    eigenvalues, eigenvectors = np.linalg.eigh(covariance_matrix)

    # np.linalg.eigh returns eigenvalues in ASCENDING order.
    # We reverse them to get descending order (PC1, PC2, ..., PCn)
    sorted_indices = np.argsort(eigenvalues)[::-1]
    sorted_eigenvalues = eigenvalues[sorted_indices]
    sorted_eigenvectors = eigenvectors[:, sorted_indices]

    # 2. Calculate the Principal Components: P = X * W
    # P is the (T x n) matrix of principal components
    principal_components = data_matrix @ sorted_eigenvectors

    # 3. Verify orthogonality of PCs (their covariance matrix should be diagonal)
    pc_covariance = np.cov(principal_components, rowvar=False)

    return sorted_eigenvalues, sorted_eigenvectors, principal_components, pc_covariance


if __name__ == "__main__":
    # --- Example Application ---
    np.random.seed(42)

    # Simulate a 3-variable correlated system (e.g., 3 interest rates)
    T = 500
    base_factor = np.random.normal(0, 1, T)

    x1 = 1.5 * base_factor + np.random.normal(0, 0.2, T)
    x2 = 1.2 * base_factor + np.random.normal(0, 0.5, T)
    x3 = 0.5 * base_factor + np.random.normal(0, 0.8, T)

    # Combine into a data matrix and center it
    X = np.column_stack((x1, x2, x3))
    X_centered = X - np.mean(X, axis=0)

    # Calculate covariance matrix
    V = np.cov(X_centered, rowvar=False)

    evals, evecs, pcs, pc_cov = calculate_principal_component_representation(V, X_centered)

    print("--- Principal Component Representation ---")
    print(f"Eigenvalues (Variance explained by each PC): {np.round(evals, 4)}")
    print(f"Total System Variance: {np.sum(evals):.4f}")
    print(f"Variance Explained by PC1: {(evals[0] / np.sum(evals)) * 100:.2f}%\n")

    print("Covariance Matrix of the Principal Components:")
    print("(Notice the off-diagonal elements are virtually zero, proving they are uncorrelated)")
    print(np.round(pc_cov, 10))
