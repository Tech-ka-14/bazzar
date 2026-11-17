"""Copula goodness-of-fit via RMSE.

Root Mean Square Error between an empirical copula surface and a fitted
parametric copula surface evaluated on the same grid; the copula with the
smaller RMSE is the better fit.
"""

import numpy as np


def calculate_copula_rmse(empirical_copula_matrix, fitted_copula_matrix):
    """
    Calculates the Root Mean Square Error (RMSE) to evaluate the goodness-of-fit
    between an empirical copula and a fitted parametric copula.

    Parameters:
    empirical_copula_matrix: 2D numpy array representing the empirical distribution values.
    fitted_copula_matrix: 2D numpy array representing the theoretical fitted distribution values.
    """
    # Ensure matrices are exactly the same shape
    if empirical_copula_matrix.shape != fitted_copula_matrix.shape:
        raise ValueError("Empirical and Fitted matrices must have the same dimensions.")

    # Calculate the squared differences
    squared_diffs = (empirical_copula_matrix - fitted_copula_matrix) ** 2

    # Calculate the mean of the squared differences
    mean_squared_error = np.mean(squared_diffs)

    # Return the root (RMSE)
    rmse = np.sqrt(mean_squared_error)

    return rmse


def compute(empirical_copula_matrix, fitted_copula_matrix) -> dict:
    """Standard facade: copula goodness-of-fit RMSE as a JSON dict.

    Parameters:
    empirical_copula_matrix: 2-D array-like of empirical copula values.
    fitted_copula_matrix: 2-D array-like of fitted copula values with the
    same shape.

    Returns:
    dict: {"grid_shape", "rmse"} with plain floats/ints.
    """
    empirical_copula_matrix = np.asarray(empirical_copula_matrix, dtype=float)
    fitted_copula_matrix = np.asarray(fitted_copula_matrix, dtype=float)
    if empirical_copula_matrix.size == 0:
        raise ValueError("matrices must be non-empty")

    rmse = calculate_copula_rmse(empirical_copula_matrix, fitted_copula_matrix)
    return {
        "grid_shape": [int(d) for d in empirical_copula_matrix.shape],
        "rmse": float(rmse),
    }


# Example Usage:
# rmse_gaussian = calculate_copula_rmse(empirical_matrix, gaussian_fitted_matrix)
# rmse_student_t = calculate_copula_rmse(empirical_matrix, student_t_fitted_matrix)
# best_model = "Gaussian" if rmse_gaussian < rmse_student_t else "Student-t"
