import numpy as np

def test_correlation_matrix_validity(matrix_list):
    """
    Tests if a matrix is a valid correlation matrix by checking if it is positive semi-definite.
    """
    C = np.array(matrix_list)
    eigenvalues = np.linalg.eigvals(C)
    
    print("Matrix:")
    print(C)
    print(f"Eigenvalues: {np.round(eigenvalues, 4)}")
    
    # A valid correlation matrix must be positive semi-definite (all eigenvalues >= 0)
    # Using a tiny tolerance for floating point errors
    tol = -1e-9
    if np.all(eigenvalues >= tol):
        print("Result: Valid correlation matrix (Positive Semi-Definite).")
    else:
        print("Result: INVALID correlation matrix (Not Positive Semi-Definite).")

def compare_eigenvalues_V_and_C(volatilities, correlation_matrix):
    """
    Demonstrates that the eigenvalues of V and C are different, 
    even though their definiteness is linked.
    """
    C = np.array(correlation_matrix)
    V = np.diag(volatilities) @ C @ np.diag(volatilities)
    
    eigenvalues_C = np.linalg.eigvals(C)
    eigenvalues_V = np.linalg.eigvals(V)
    
    print("\n--- Eigenvalue Comparison ---")
    print(f"Eigenvalues of Correlation Matrix C: {np.round(np.sort(eigenvalues_C)[::-1], 4)}")
    print(f"Eigenvalues of Covariance Matrix V: {np.round(np.sort(eigenvalues_V)[::-1], 4)}")

# --- Testing with Examples from the text ---
if __name__ == "__main__":
    # Example I.2.13: A non-positive definite 3x3 matrix
    print("--- Example I.2.13: Testing Matrix Validity ---")
    invalid_C = [
        [1.0, -0.9, -0.8],
        [-0.9, 1.0, -0.5],
        [-0.8, -0.5, 1.0]
    ]
    test_correlation_matrix_validity(invalid_C)
    
    # Example I.2.14: Eigenvectors and Eigenvalues of a 2x2 Covariance Matrix
    vols = [0.20, 0.25]
    C_matrix = [
        [1.0, 0.5],
        [0.5, 1.0]
    ]
    
    print("\n--- Example I.2.14 ---")
    compare_eigenvalues_V_and_C(vols, C_matrix)