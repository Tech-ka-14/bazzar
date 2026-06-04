import numpy as np

def evaluate_quadratic_form(x_list, A_list):
    """
    Evaluates the quadratic form x'Ax.
    """
    x = np.array(x_list)
    A = np.array(A_list)
    
    # x.T @ A @ x is the pythonic way to write x'Ax using matrix multiplication
    result = x.T @ A @ x
    return result

def test_definiteness(A_list):
    """
    Tests if a symmetric matrix A is positive definite, positive semi-definite,
    negative definite, or negative semi-definite using eigenvalues.
    """
    A = np.array(A_list)
    
    # Step 1: Ensure the matrix is symmetric for the test to be valid
    # B = 0.5 * (A + A')
    B = 0.5 * (A + A.T)
    
    # Step 2: Calculate eigenvalues
    eigenvalues = np.linalg.eigvals(B)
    
    # Step 3: Check conditions
    # Using a small tolerance to handle floating point inaccuracies near zero
    tol = 1e-9
    
    is_pos_def = np.all(eigenvalues > tol)
    is_pos_semi_def = np.all(eigenvalues >= -tol) and not is_pos_def
    is_neg_def = np.all(eigenvalues < -tol)
    is_neg_semi_def = np.all(eigenvalues <= tol) and not is_neg_def
    
    print(f"Matrix Symmetric Equivalent B:\n{B}")
    print(f"Eigenvalues: {np.round(eigenvalues, 4)}")
    
    if is_pos_def:
        print("Result: The matrix is POSITIVE DEFINITE.")
    elif is_pos_semi_def:
        print("Result: The matrix is POSITIVE SEMI-DEFINITE.")
    elif is_neg_def:
        print("Result: The matrix is NEGATIVE DEFINITE.")
    elif is_neg_semi_def:
        print("Result: The matrix is NEGATIVE SEMI-DEFINITE.")
    else:
        print("Result: The matrix is INDEFINITE (neither positive nor negative definite).")

# --- Testing with Examples from the text ---
if __name__ == "__main__":
    A_matrix = [
        [1, -2, 3],
        [2, 4, 0],
        [0, 2, -1]
    ]
    
    # Example I.2.5 (a)
    x_vector = [0.5, 0.3, 0.2]
    q_form = evaluate_quadratic_form(x_vector, A_matrix)
    print(f"--- Quadratic Form (Example I.2.5 a) ---\nResult: {q_form:.2f}\n")
    
    # Example I.2.7
    A_matrix_2 = [
        [1, 1, 2],
        [1, 5, -4],
        [-2, -4, 6]
    ]
    print("--- Definiteness Test (Example I.2.7) ---")
    test_definiteness(A_matrix_2)