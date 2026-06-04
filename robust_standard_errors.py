import numpy as np

def whites_robust_covariance(X, residuals):
    """
    Calculates White's Heteroscedasticity-Consistent Covariance Matrix.
    
    Parameters:
    X (numpy.ndarray): Explanatory variables matrix (T x k), including constant.
    residuals (numpy.ndarray): OLS residuals vector (T x 1).
    
    Returns:
    numpy.ndarray: White's robust covariance matrix for the estimated coefficients.
    """
    T, k = X.shape
    
    # Calculate (X'X)^-1
    XX_inv = np.linalg.inv(X.T @ X)
    
    # Calculate Sigma: the sum of e_t^2 * (x_t * x_t') divided by T
    Sigma = np.zeros((k, k))
    for t in range(T):
        x_t = X[t, :].reshape(-1, 1)  # Column vector for observation t
        e_t_sq = residuals[t] ** 2
        Sigma += e_t_sq * (x_t @ x_t.T)
        
    Sigma /= T
    
    # Calculate White's Robust Covariance Matrix: T * (X'X)^-1 * Sigma * (X'X)^-1
    robust_cov = T * (XX_inv @ Sigma @ XX_inv)
    
    return robust_cov

if __name__ == "__main__":
    # Synthetic Data Setup
    np.random.seed(42)
    T = 100
    X = np.column_stack((np.ones(T), np.random.normal(0, 1, T)))
    residuals = np.random.normal(0, 1, T) * X[:, 1] # Introduce heteroscedasticity
    
    robust_cov_matrix = whites_robust_covariance(X, residuals)
    robust_std_errors = np.sqrt(np.diag(robust_cov_matrix))
    
    print("White's Robust Standard Errors:")
    print(np.round(robust_std_errors, 4))