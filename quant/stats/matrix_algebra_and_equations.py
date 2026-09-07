import numpy as np


def solve_homogeneous_system(matrix_list):
    """
    Solves a homogeneous system Ax = 0 and analyzes its solutions based on the determinant.
    """
    A = np.array(matrix_list)
    det_A = np.linalg.det(A)
    n = A.shape[0]

    print(f"Matrix A:\n{A}")
    print(f"Determinant of A: {det_A:.4f}")

    if abs(det_A) > 1e-10:
        # Determinant is non-zero: A is non-singular
        print("Conclusion: Unique solution exists (the trivial solution x = 0).")
        solution = np.zeros(n)
        print(f"Solution x: {solution}")
    else:
        # Determinant is zero: A is singular
        print("Conclusion: Infinitely many solutions exist (A is singular).")
        # Finding the null space of A to provide an example of a non-trivial solution
        # Using SVD to find the null space vector
        U, S, Vh = np.linalg.svd(A)
        # The last row of Vh corresponds to the smallest singular value (the null space)
        null_space_vector = Vh[-1, :]
        print(f"Example of a non-trivial solution x: {np.round(null_space_vector, 4)}")


# --- Testing with Examples from the text ---
if __name__ == "__main__":
    # Example I.2.4: Unique solution (det != 0)
    print("--- Example I.2.4 ---")
    A1 = [[1, -3, 2], [2, -5, 3], [-3, 8, -4]]
    solve_homogeneous_system(A1)

    print("\n" + "=" * 40 + "\n")

    # Example I.2.5: Infinitely many solutions (det = 0)
    print("--- Example I.2.5 ---")
    A2 = [[1, -3, 2], [2, -6, 4], [-3, 9, -6]]
    solve_homogeneous_system(A2)
