"""Eigen decomposition of a square matrix.

Eigenvalues and normalized eigenvectors (columns), sorted by descending
eigenvalue as is standard in PCA. Reference: Alexander (2008), Vol. I,
Examples I.2.8-I.2.10.
"""

import numpy as np


def calculate_eigen_decomposition(matrix_list):
    """
    Calculates the eigenvalues and normalized eigenvectors of a square matrix.
    """
    A = np.array(matrix_list)

    # Check if matrix is square
    if A.shape[0] != A.shape[1]:
        raise ValueError("Eigenvalue decomposition requires a square matrix.")

    # np.linalg.eig returns eigenvalues and normalized eigenvectors
    # Note: Eigenvectors are returned as columns in the 'vectors' matrix
    eigenvalues, eigenvectors = np.linalg.eig(A)

    # Sort them in descending order of eigenvalue magnitude (standard practice in PCA)
    sorted_indices = np.argsort(eigenvalues)[::-1]
    sorted_eigenvalues = eigenvalues[sorted_indices]
    sorted_eigenvectors = eigenvectors[:, sorted_indices]

    print("Matrix A:")
    print(A)
    print("\nEigenvalues (λ):")
    print(np.round(sorted_eigenvalues, 4))

    print("\nNormalized Eigenvectors (w) as columns:")
    print(np.round(sorted_eigenvectors, 4))

    return sorted_eigenvalues, sorted_eigenvectors


def compute(data) -> dict:
    """Standard facade: eigen decomposition as a JSON-serializable dict.

    Parameters:
    data: square matrix (list of lists) with real eigenvalues.

    Returns:
    dict: {"eigenvalues", "eigenvectors"} sorted by descending eigenvalue;
    eigenvectors are the columns of the returned matrix.
    """
    A = np.asarray(data, dtype=float)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError("data must be a square matrix")

    eigenvalues, eigenvectors = np.linalg.eig(A)
    if np.any(np.abs(eigenvalues.imag) > 1e-12):
        raise ValueError("matrix has complex eigenvalues; not JSON-serializable")
    idx = np.argsort(eigenvalues.real)[::-1]
    return {
        "eigenvalues": [float(v) for v in eigenvalues.real[idx]],
        "eigenvectors": eigenvectors.real[:, idx].tolist(),
    }


# --- Testing with Examples from the text ---
if __name__ == "__main__":
    # Example I.2.8: A non-symmetric 2x2 matrix
    print("--- Example I.2.8 ---")
    A_matrix = [[2, -1], [-2, 3]]
    calculate_eigen_decomposition(A_matrix)

    # Example I.2.10: A 3x3 correlation matrix
    print("\n--- Example I.2.10 (Correlation Matrix) ---")
    C_matrix = [[1, 0.5, 0.2], [0.5, 1, 0.3], [0.2, 0.3, 1]]
    calculate_eigen_decomposition(C_matrix)
