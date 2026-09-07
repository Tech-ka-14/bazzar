import numpy as np


def principal_component_analysis(covariance_matrix):
    """
    Performs PCA on a given covariance or correlation matrix.

    Parameters:
    covariance_matrix (numpy.ndarray): A symmetric, positive semi-definite matrix (n x n).

    Returns:
    tuple: (eigenvalues, eigenvectors, explained_variance_ratio)
           Eigenvalues are sorted in descending order.
    """
    # 1. Perform Eigen-decomposition
    # np.linalg.eigh is optimized for symmetric matrices like covariance matrices
    eigenvalues, eigenvectors = np.linalg.eigh(covariance_matrix)

    # 2. Sort eigenvalues and corresponding eigenvectors in descending order
    sorted_indices = np.argsort(eigenvalues)[::-1]
    sorted_eigenvalues = eigenvalues[sorted_indices]
    sorted_eigenvectors = eigenvectors[:, sorted_indices]

    # 3. Calculate the proportion of variance explained by each principal component
    total_variance = np.sum(sorted_eigenvalues)
    explained_variance_ratio = sorted_eigenvalues / total_variance

    return sorted_eigenvalues, sorted_eigenvectors, explained_variance_ratio


if __name__ == "__main__":
    # --- Example Application: PCA on a 3-Asset Correlation Matrix ---
    # A typical correlation matrix for 3 financial assets
    corr_matrix = np.array([[1.0, 0.8, 0.5], [0.8, 1.0, 0.4], [0.5, 0.4, 1.0]])

    evals, evecs, explained_ratio = principal_component_analysis(corr_matrix)

    print("--- Principal Component Analysis (PCA) ---")
    print("Eigenvalues:")
    print(np.round(evals, 4))
    print("\nEigenvectors (Columns represent the components):")
    print(np.round(evecs, 4))
    print("\nProportion of Variance Explained:")
    for i, ratio in enumerate(explained_ratio):
        print(f"PC{i + 1}: {ratio * 100:.2f}%")
