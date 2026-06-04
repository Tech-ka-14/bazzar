import numpy as np
import scipy.stats as stats

def quantile_var_se(alpha: float, T: int, quantile_val: float, h: int, sigma_daily: float) -> float:
    """
    Approximates the standard error of a Simulation/Historical VaR quantile.
    This requires evaluating the Probability Density Function (PDF) at the quantile.
    
    For demonstration, we evaluate the PDF assuming the underlying true distribution 
    is Normal with mean 0 and standard deviation scaled for h days.
    """
    # True h-day standard deviation
    sigma_h = sigma_daily * np.sqrt(h)
    
    # Evaluate the PDF f(x) at the quantile value
    # Note: VaR is typically positive, but the actual quantile value is negative
    f_q = stats.norm.pdf(-quantile_val, loc=0, scale=sigma_h)
    
    # Calculate standard error
    se = (1 / f_q) * np.sqrt((alpha * (1 - alpha)) / T)
    return se

# Example usage from Example IV.6.4
var_quantile_se = quantile_var_se(alpha=0.01, T=1000, quantile_val=var_10d, h=10, sigma_daily=0.20)