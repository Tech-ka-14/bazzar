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
    squared_diffs = (empirical_copula_matrix - fitted_copula_matrix)**2
    
    # Calculate the mean of the squared differences
    mean_squared_error = np.mean(squared_diffs)
    
    # Return the root (RMSE)
    rmse = np.sqrt(mean_squared_error)
    
    return rmse

# Example Usage:
# rmse_gaussian = calculate_copula_rmse(empirical_matrix, gaussian_fitted_matrix)
# rmse_student_t = calculate_copula_rmse(empirical_matrix, student_t_fitted_matrix)
# best_model = "Gaussian" if rmse_gaussian < rmse_student_t else "Student-t"