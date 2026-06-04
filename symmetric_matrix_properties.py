import numpy as np

def analyze_2x2_correlation_matrix(r):
    """
    Demonstrates the exact analytical eigenvalues and eigenvectors for a 2x2 correlation matrix.
    """
    print(f"Analyzing 2x2 Correlation Matrix with r = {r}")
    
    # Analytical eigenvalues
    lambda_1 = 1 + r
    lambda_2 = 1 - r
    print(f"Analytical Eigenvalues: {lambda_1}, {lambda_2}")
    
    # Analytical normalized eigenvectors
    w_1 = np.array([1/np.sqrt(2), 1/np.sqrt(2)])
    w_2 = np.array([1/np.sqrt(2), -1/np.sqrt(2)])
    print(f"Analytical Eigenvector 1: {np.round(w_1, 4)}")
    print(f"Analytical Eigenvector 2: {np.round(w_2, 4)}")

def verify_orthogonality(matrix_list):
    """
    Verifies that the eigenvectors of a symmetric matrix are orthogonal, 
    and that the eigenvector matrix W satisfies W^(-1) = W'.
    """
    A = np.array(matrix_list)
    
    # np.linalg.eigh is optimized for Hermitian (symmetric) matrices
    eigenvalues, W = np.linalg.eigh(A)
    
    print("\nMatrix of Eigenvectors (W):")
    print(np.round(W, 4))
    
    # 1. Verify dot product of distinct eigenvectors is 0 (Orthogonality)
    # Taking the first and second columns (eigenvectors)
    w1 = W[:, 0]
    w2 = W[:, 1]
    dot_product = np.dot(w1, w2)
    print(f"\nDot product of Eigenvector 1 and Eigenvector 2: {dot_product:.10f}")
    if np.isclose(dot_product, 0.0):
        print("-> The eigenvectors are orthogonal.")
        
    # 2. Verify W^(-1) == W'
    W_inv = np.linalg.inv(W)
    W_trans = W.T
    
    print("\nInverse of W (W^-1):")
    print(np.round(W_inv, 4))
    print("\nTranspose of W (W'):")
    print(np.round(W_trans, 4))
    
    if np.allclose(W_inv, W_trans):
        print("-> Verified: W^(-1) is equal to W' (W is an orthogonal matrix).")

# --- Testing the properties ---
if __name__ == "__main__":
    # Test 2x2 Correlation Matrix (r = 0.75)
    analyze_2x2_correlation_matrix(0.75)
    
    # Test Orthogonality with a symmetric 3x3 matrix
    print("\n--- Verifying Orthogonal Properties ---")
    symmetric_matrix = [
        [1, 0.5, 0.2],
        [0.5, 1, 0.3],
        [0.2, 0.3, 1]
    ]
    verify_orthogonality(symmetric_matrix)