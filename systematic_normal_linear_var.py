import numpy as np
from scipy.stats import norm

def calculate_systematic_var(theta: np.ndarray, omega_h: np.ndarray, 
                             mu_h: np.ndarray = None, alpha: float = 0.01) -> float:
    """
    Calculates the Systematic Normal Linear VaR using matrix algebra.
    
    Parameters:
    theta (np.ndarray): The risk factor sensitivity vector (m x 1).
    omega_h (np.ndarray): The h-day covariance matrix of risk factor returns (m x m).
    mu_h (np.ndarray, optional): The vector of expected excess returns (m x 1). Defaults to zero drift.
    alpha (float): The significance level (e.g., 0.01 for 99% confidence).
    
    Returns:
    float: The Systematic VaR.
    """
    # Calculate portfolio variance: theta' * Omega * theta
    variance = theta.T @ omega_h @ theta
    volatility = np.sqrt(variance)
    
    # Standard normal critical value
    critical_value = norm.ppf(1 - alpha)
    
    # Calculate base VaR
    var_base = critical_value * volatility
    
    # Apply drift adjustment if mu_h is provided (Eq. IV.2.14)
    if mu_h is not None:
        expected_return = theta.T @ mu_h
        return var_base - expected_return
        
    # Return zero-drift VaR (Eq. IV.2.15)
    return var_base

# Example Usage
theta_vec = np.array([0.5, 0.3, 0.2])  # Sensitivities to 3 factors
omega_mat = np.array([
    [0.0004, 0.0001, 0.00005],
    [0.0001, 0.0009, 0.0002],
    [0.00005, 0.0002, 0.0016]
])

sys_var = calculate_systematic_var(theta_vec, omega_mat, alpha=0.01)
print(f"1% Systematic VaR (Zero Drift): {sys_var:.4%}")