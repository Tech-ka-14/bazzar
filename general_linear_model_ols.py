import numpy as np

def multiple_regression_ols(y_data, x_matrix):
    """
    Fits a General Linear Model (Multiple Regression) using pure matrix algebra.
    
    Parameters:
    y_data : list or 1D numpy array of dependent variable observations (T x 1)
    x_matrix : 2D list or numpy array of explanatory variables (T x (k-1)).
               The constant term (column of 1s) will be added automatically.
    """
    T = len(y_data)
    y = np.array(y_data).reshape(T, 1)
    
    # 1. Setup the Design Matrix X (T x k)
    # Convert input features to a numpy array and prepend a column of 1s for the intercept (beta_1)
    x_features = np.array(x_matrix)
    
    # Ensure x_features is 2D even if only one variable is passed
    if x_features.ndim == 1:
        x_features = x_features.reshape(T, 1)
        
    k = x_features.shape[1] + 1 # Total parameters = number of features + 1 (intercept)
    X = np.column_stack((np.ones(T), x_features))
    
    # 2. Calculate the OLS Estimator: beta_hat = (X'X)^-1 X'y
    X_prime_X = X.T @ X
    X_prime_X_inv = np.linalg.inv(X_prime_X)
    X_prime_y = X.T @ y
    
    beta_hat = X_prime_X_inv @ X_prime_y
    
    # 3. Calculate Residuals and Error Variance
    # y_hat = X * beta_hat
    y_hat = X @ beta_hat
    
    # residuals e = y - y_hat
    residuals = y - y_hat
    
    # RSS = e'e
    rss = (residuals.T @ residuals)[0, 0]
    
    # Estimated error variance (sigma^2 estimator) = RSS / (T - k)
    sigma_squared_est = rss / (T - k)
    
    # 4. Calculate the Covariance Matrix of Estimators: V(beta_hat) = sigma^2 * (X'X)^-1
    cov_matrix_beta = sigma_squared_est * X_prime_X_inv
    
    # Standard errors are the square roots of the diagonal elements
    standard_errors = np.sqrt(np.diag(cov_matrix_beta))
    
    results = {
        'coefficients': beta_hat.flatten(),
        'covariance_matrix': cov_matrix_beta,
        'standard_errors': standard_errors,
        'rss': rss,
        'degrees_of_freedom': T - k
    }
    
    return results

# --- Example Usage for a Multivariate Model ---
# Let's assume a dataset with T=10 observations and 2 explanatory variables (X2 and X3)
Y_observed = [5.1, 6.2, 7.3, 8.1, 9.5, 10.2, 11.0, 12.1, 13.5, 14.2]

# Matrix of explanatory variables (without the constant term)
X_observed = [
    [1.0, 2.5],
    [2.0, 2.8],
    [3.0, 3.1],
    [3.5, 3.8],
    [4.0, 4.2],
    [5.0, 4.5],
    [5.5, 5.0],
    [6.0, 5.5],
    [7.0, 6.0],
    [7.5, 6.5]
]

print("--- General Linear Model Estimation (Multiple Regression) ---")
results = multiple_regression_ols(Y_observed, X_observed)

print("Estimated Coefficients (beta):")
print(f"Intercept (beta_1): {results['coefficients'][0]:.4f}")
print(f"Slope X2 (beta_2):  {results['coefficients'][1]:.4f}")
print(f"Slope X3 (beta_3):  {results['coefficients'][2]:.4f}\n")

print("Standard Errors:")
print(np.round(results['standard_errors'], 4))

print("\nCovariance Matrix of Estimators:")
print(np.round(results['covariance_matrix'], 4))