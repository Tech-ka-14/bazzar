"""Matrix algebra and linear equation systems.

Transpose, determinant and inverse of a square matrix, and the solution of
simultaneous linear systems Ax = b. Reference: Alexander (2008), Vol. I,
Examples I.2.3-I.2.4.
"""

import numpy as np


def analyze_matrix(A_list):
    """
    Computes the transpose, determinant, and inverse of a given square matrix A.
    """
    A = np.array(A_list)

    print("Matrix A:")
    print(A)

    print("\nTranspose A':")
    print(A.T)

    # Check if the matrix is square
    if A.shape[0] == A.shape[1]:
        det_A = np.linalg.det(A)
        print(f"\nDeterminant |A|: {det_A:.4f}")

        # A matrix is only invertible if its determinant is non-zero
        if not np.isclose(det_A, 0.0):
            inv_A = np.linalg.inv(A)
            print("\nInverse A^(-1):")
            print(np.round(inv_A, 4))
        else:
            print("\nMatrix is singular (Determinant is 0). No inverse exists.")
    else:
        print("\nMatrix is not square. Determinant and Inverse are undefined.")


def solve_linear_system(A_list, b_list):
    """
    Solves a system of simultaneous linear equations: Ax = b.
    """
    A = np.array(A_list)
    b = np.array(b_list)

    try:
        # np.linalg.solve is numerically more stable/efficient than computing the inverse directly
        x = np.linalg.solve(A, b)
        print("\nSolution Vector x:")
        print(x)
        return x
    except np.linalg.LinAlgError:
        print("\nThe coefficient matrix A is singular. The system does not have a unique solution.")
        return None


def compute(data, b=None) -> dict:
    """Standard facade: matrix analysis and linear-system solution.

    Parameters:
    data: matrix (list of lists).
    b (array-like, optional): right-hand side for solving Ax = b (square A).

    Returns:
    dict: {"square", "transpose", "determinant", "inverse"} plus
    {"solution"} when b is given (None values when undefined).
    """
    A = np.asarray(data, dtype=float)
    if A.ndim != 2:
        raise ValueError("data must be a 2-D matrix")

    out = {"transpose": A.T.tolist()}
    if A.shape[0] != A.shape[1]:
        if b is not None:
            raise ValueError("solving Ax = b requires a square matrix")
        out.update({"square": False, "determinant": None, "inverse": None})
        return out

    determinant = float(np.linalg.det(A))
    out["square"] = True
    out["determinant"] = determinant
    out["inverse"] = None if np.isclose(determinant, 0.0) else np.linalg.inv(A).tolist()
    if b is not None:
        solution = solve_linear_system(A, np.asarray(b, dtype=float))
        out["solution"] = None if solution is None else np.asarray(solution).tolist()
    return out


# --- Testing with Examples from the text ---
if __name__ == "__main__":
    # Example I.2.3 and I.2.4
    A_matrix = [[1, -2, 3], [2, 4, 0], [0, 2, -1]]
    b_vector = [1, 3, 0]

    print("--- Matrix Analysis (Example I.2.3) ---")
    analyze_matrix(A_matrix)

    print("\n--- Solving Simultaneous Equations (Example I.2.4) ---")
    solve_linear_system(A_matrix, b_vector)
