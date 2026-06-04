import numpy as np
import pandas as pd

def calculate_ewma_metrics(returns_x, returns_y, lambda_param=0.94):
    """
    Calculates recursive EWMA variance, covariance, correlation, and beta 
    for two return series using a specified decay parameter (lambda).
    """
    T = len(returns_x)
    
    # Initialize arrays
    var_x = np.zeros(T)
    var_y = np.zeros(T)
    cov_xy = np.zeros(T)
    
    # Set initial values (using standard variance/covariance of the first few days or entire sample)
    var_x[0] = np.var(returns_x)
    var_y[0] = np.var(returns_y)
    cov_xy[0] = np.cov(returns_x, returns_y)[0, 1]
    
    # Recursive calculation
    for t in range(1, T):
        # Variance recursion
        var_x[t] = (1 - lambda_param) * returns_x[t-1]**2 + lambda_param * var_x[t-1]
        var_y[t] = (1 - lambda_param) * returns_y[t-1]**2 + lambda_param * var_y[t-1]
        
        # Covariance recursion
        cov_xy[t] = (1 - lambda_param) * (returns_x[t-1] * returns_y[t-1]) + lambda_param * cov_xy[t-1]
        
    # Derived metrics
    volatility_x = np.sqrt(var_x)
    volatility_y = np.sqrt(var_y)
    correlation_xy = cov_xy / (volatility_x * volatility_y)
    beta_y_to_x = cov_xy / var_x  # Assuming X is the market
    
    return pd.DataFrame({
        'EWMA_Var_X': var_x,
        'EWMA_Var_Y': var_y,
        'EWMA_Cov_XY': cov_xy,
        'EWMA_Correlation': correlation_xy,
        'EWMA_Beta': beta_y_to_x
    })