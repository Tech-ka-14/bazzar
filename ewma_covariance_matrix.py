import numpy as np

def calculate_ewma_covariance(returns_1: np.ndarray, returns_2: np.ndarray, 
                              lambda_param: float, initial_cov: float = None) -> np.ndarray:
    """
    Calculates the time series of EWMA covariance using the recursive formula (Equation IV.2.81).
    """
    n = len(returns_1)
    ewma_cov = np.zeros(n)
    
    ewma_cov[0] = initial_cov if initial_cov is not None else np.cov(returns_1, returns_2)[0, 1]
    
    for t in range(1, n):
        ewma_cov[t] = (1 - lambda_param) * (returns_1[t-1] * returns_2[t-1]) + (lambda_param * ewma_cov[t-1])
        
    return ewma_cov

def build_ewma_covariance_matrix(returns_matrix: np.ndarray, lambda_param: float) -> np.ndarray:
    """
    Constructs the final EWMA covariance matrix for the most recent time step t.
    returns_matrix shape should be (num_assets, num_timesteps)
    """
    num_assets, n_steps = returns_matrix.shape
    ewma_matrix_t = np.zeros((num_assets, num_assets))
    
    for i in range(num_assets):
        for j in range(num_assets):
            if i == j:
                # Calculate variance
                var_series = calculate_ewma_variance(returns_matrix[i], lambda_param)
                ewma_matrix_t[i, j] = var_series[-1]
            else:
                # Calculate covariance
                cov_series = calculate_ewma_covariance(returns_matrix[i], returns_matrix[j], lambda_param)
                ewma_matrix_t[i, j] = cov_series[-1]
                
    return ewma_matrix_t

# Mock data for S&P 500 and NDX (Table IV.2.32)
np.random.seed(42)
ret_sp500 = np.random.normal(0, 0.012, 500)
ret_ndx = ret_sp500 * 1.2 + np.random.normal(0, 0.005, 500) # Correlated returns

asset_returns = np.array([ret_sp500, ret_ndx])

# Build the dynamic RiskMetrics Daily Matrix
daily_matrix_lambda = 0.94
ewma_cov_matrix = build_ewma_covariance_matrix(asset_returns, daily_matrix_lambda)

print("Current Daily EWMA Covariance Matrix (lambda=0.94):")
print(ewma_cov_matrix)