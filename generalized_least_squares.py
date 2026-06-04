import numpy as np

def generalized_least_squares(X, y, Omega):
    """
    Performs Generalized Least Squares (GLS) regression.
    
    Parameters:
    X (numpy.ndarray): Explanatory variables matrix (T x k).
    y (numpy.ndarray): Dependent variable vector (T x 1).
    Omega (numpy.ndarray): The known covariance structure of the error process (T x T).
    
    Returns:
    tuple: GLS estimators (beta_hat) and their estimated covariance matrix.
    """
    T, k = X.shape
    
    # Inverse of the error covariance structure
    Omega_inv = np.linalg.inv(Omega)
    
    # 1. Calculate GLS Estimators: (X' Omega^-1 X)^-1 * (X' Omega^-1 y)
    X_Omega_X_inv = np.linalg.inv(X.T @ Omega_inv @ X)
    beta_hat_GLS = X_Omega_X_inv @ (X.T @ Omega_inv @ y)
    
    # 2. Calculate Residuals to estimate sigma^2
    residuals = y - (X @ beta_hat_GLS)
    
    # For GLS, the residual variance estimator accounts for Omega^-1
    sigma_squared = (residuals.T @ Omega_inv @ residuals) / (T - k)
    if isinstance(sigma_squared, np.ndarray):
        sigma_squared = sigma_squared.item()
        
    # 3. Calculate Covariance Matrix of GLS estimators
    cov_matrix_GLS = sigma_squared * X_Omega_X_inv
    
    return beta_hat_GLS.flatten(), cov_matrix_GLS, sigma_squared

if __name__ == "__main__":
    np.random.seed(42)
    T = 100
    
    X = np.column_stack((np.ones(T), np.random.normal(0, 1, T)))
    true_beta = np.array([2.0, 3.5])
    
    # Simulate a heteroscedastic structure (variance grows with index)
    variances = np.linspace(1, 5, T)
    Omega_hetero = np.diag(variances)
    
    # Generate dependent variable with heteroscedastic noise
    noise = np.random.normal(0, np.sqrt(variances))
    y = X @ true_beta + noise
    
    beta_gls, cov_gls, sig_sq = generalized_least_squares(X, y, Omega_hetero)
    
    print("--- Generalized Least Squares (GLS) ---")
    print(f"True Beta: {true_beta}")
    print(f"GLS Estimated Beta: {np.round(beta_gls, 4)}")
    print(f"GLS Standard Errors: {np.round(np.sqrt(np.diag(cov_gls)), 4)}")