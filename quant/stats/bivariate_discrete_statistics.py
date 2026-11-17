"""Bivariate discrete probability distributions.

Computes marginal expectations, variances, covariance and correlation from a
joint probability matrix. Reference: Alexander (2008), Vol. I,
Examples I.3.10-I.3.11.
"""

import numpy as np


def calculate_bivariate_statistics(x_values, y_values, joint_probabilities):
    """
    Calculates marginal expectations, variance, covariance, and correlation
    from a discrete bivariate probability distribution.
    """
    P = np.array(joint_probabilities)
    X = np.array(x_values)
    Y = np.array(y_values)

    # 1. Marginal Probabilities (Summing across rows/cols)
    P_X = np.sum(P, axis=0)  # Sum over Y
    P_Y = np.sum(P, axis=1)  # Sum over X

    # 2. Marginal Expectations: E(X) and E(Y)
    mu_X = np.sum(X * P_X)
    mu_Y = np.sum(Y * P_Y)

    # 3. Variances: E(X^2) - E(X)^2
    var_X = np.sum((X**2) * P_X) - (mu_X**2)
    var_Y = np.sum((Y**2) * P_Y) - (mu_Y**2)

    # 4. Covariance: E(XY) - E(X)E(Y)
    # E(XY) is calculated by creating a grid of X*Y and multiplying by joint probabilities
    X_grid, Y_grid = np.meshgrid(X, Y)
    E_XY = np.sum(X_grid * Y_grid * P)

    covariance = E_XY - (mu_X * mu_Y)

    # 5. Correlation: Cov(X,Y) / (Std(X)*Std(Y))
    correlation = covariance / np.sqrt(var_X * var_Y)

    print(f"Expectations -> E(X): {mu_X:.2f}, E(Y): {mu_Y:.2f}")
    print(f"Variances -> V(X): {var_X:.2f}, V(Y): {var_Y:.2f}")
    print(f"Covariance: {covariance:.2f}")
    print(f"Correlation: {correlation:.4f}")

    return mu_X, mu_Y, var_X, var_Y, covariance, correlation


def compute(data, y_values=None, joint_probabilities=None) -> dict:
    """Standard facade: bivariate discrete statistics as a JSON-serializable dict.

    Parameters:
    data: sequence of x values.
    y_values: sequence of y values.
    joint_probabilities: (len(y), len(x)) joint probability matrix summing to 1.

    Returns:
    dict: {"e_x", "e_y", "var_x", "var_y", "covariance", "correlation"}.
    """
    if y_values is None or joint_probabilities is None:
        raise ValueError("y_values and joint_probabilities are required")
    X = np.asarray(data, dtype=float).ravel()
    Y = np.asarray(y_values, dtype=float).ravel()
    P = np.asarray(joint_probabilities, dtype=float)
    if P.shape != (Y.size, X.size):
        raise ValueError("joint_probabilities must have shape (len(y_values), len(data))")
    if not np.isclose(P.sum(), 1.0):
        raise ValueError("joint probabilities must sum to 1")

    P_X = np.sum(P, axis=0)
    P_Y = np.sum(P, axis=1)
    mu_X = float(np.sum(X * P_X))
    mu_Y = float(np.sum(Y * P_Y))
    var_X = float(np.sum((X**2) * P_X) - mu_X**2)
    var_Y = float(np.sum((Y**2) * P_Y) - mu_Y**2)
    X_grid, Y_grid = np.meshgrid(X, Y)
    covariance = float(np.sum(X_grid * Y_grid * P) - mu_X * mu_Y)
    return {
        "e_x": mu_X,
        "e_y": mu_Y,
        "var_x": var_X,
        "var_y": var_Y,
        "covariance": covariance,
        "correlation": float(covariance / np.sqrt(var_X * var_Y)),
    }


# --- Testing with Examples I.3.10 and I.3.11 from the text ---
if __name__ == "__main__":
    print("--- Example I.3.10 & I.3.11: Bivariate Statistics ---")
    x_vals = [-20, -10, 5, 10, 20]
    y_vals = [0, -20, 40, 30, -10]

    # Joint probabilities matching Table I.3.6
    # Note: The table maps specific (x,y) pairs. To represent this as a matrix,
    # we place the probabilities where X and Y intersect, and 0 elsewhere.
    joint_prob_matrix = np.zeros((len(y_vals), len(x_vals)))
    # P(X=-20, Y=0) = 0.2
    joint_prob_matrix[0, 0] = 0.2
    # P(X=-10, Y=-20) = 0.1
    joint_prob_matrix[1, 1] = 0.1
    # P(X=5, Y=40) = 0.3
    joint_prob_matrix[2, 2] = 0.3
    # P(X=10, Y=30) = 0.25
    joint_prob_matrix[3, 3] = 0.25
    # P(X=20, Y=-10) = 0.15
    joint_prob_matrix[4, 4] = 0.15

    calculate_bivariate_statistics(x_vals, y_vals, joint_prob_matrix)
