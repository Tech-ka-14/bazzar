import numpy as np
import scipy.stats as stats

def calculate_normal_var(sigma: float, h: int, alpha: float) -> float:
    """Calculates the normal linear VaR."""
    # Note: alpha here is the tail probability (e.g., 0.01 for 1%)
    z_score = stats.norm.ppf(1 - alpha)
    return z_score * sigma * np.sqrt(h)

def var_se_equally_weighted(var_estimate: float, T: int) -> float:
    """
    Approximates the standard error of a Normal VaR estimate 
    using an equally weighted volatility model.
    """
    return var_estimate / np.sqrt(2 * T)

def var_se_ewma(var_estimate: float, lambda_param: float) -> float:
    """
    Approximates the standard error of a Normal VaR estimate 
    using an EWMA volatility model.
    """
    return var_estimate * np.sqrt((1 - lambda_param) / (2 * (1 + lambda_param)))

# Example usage based on Table IV.6.5 (sigma = 0.20, h = 10, alpha = 0.01)
sigma = 0.20
h = 10
alpha = 0.01

var_10d = calculate_normal_var(sigma, h, alpha)
se_eq_weighted = var_se_equally_weighted(var_10d, T=100)
se_ewma = var_se_ewma(var_10d, lambda_param=0.94)