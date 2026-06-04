import numpy as np
from scipy.stats import norm

def cornish_fisher_quantile(alpha: float, skewness: float, excess_kurtosis: float) -> float:
    """
    Calculates the Cornish-Fisher approximation to the alpha quantile 
    of a normalized empirical distribution. (Equation IV.3.7)
    """
    z_alpha = norm.ppf(alpha)
    
    # 1st order adjustment (Skewness)
    term_2 = (skewness / 6.0) * ((z_alpha ** 2) - 1)
    
    # 2nd order adjustment (Kurtosis)
    term_3 = (excess_kurtosis / 24.0) * z_alpha * ((z_alpha ** 2) - 3)
    
    # 3rd order adjustment (Skewness squared interaction)
    term_4 = ((skewness ** 2) / 36.0) * z_alpha * ((2 * z_alpha ** 2) - 5)
    
    x_tilde_alpha = z_alpha + term_2 + term_3 - term_4
    return x_tilde_alpha

def calculate_cornish_fisher_var(alpha: float, mu_annual: float, vol_annual: float, 
                                 skewness: float, excess_kurtosis: float, 
                                 h_days: int = 10, days_in_year: int = 250) -> float:
    """
    Estimates the scaled VaR using the Cornish-Fisher expansion. (Equation IV.3.8)
    """
    # Calculate the normalized quantile
    x_tilde = cornish_fisher_quantile(alpha, skewness, excess_kurtosis)
    
    # Scale annualized mean and volatility to the risk horizon
    time_scale = h_days / days_in_year
    mu_h = mu_annual * time_scale
    vol_h = vol_annual * np.sqrt(time_scale)
    
    # Scale back to the empirical distribution's mean and standard deviation
    x_alpha = (x_tilde * vol_h) + mu_h
    
    # VaR is the negative of the loss quantile
    return -x_alpha

# Example IV.3.4: Cornish-Fisher Approximation
# Table IV.3.11 Parameters
mu_ann = 0.05
vol_ann = 0.10
skew = -0.6
exc_kurtosis = 3.0

horizon = 10
conf_level = 0.01 # Looking at the 1% lower tail

# 1. Standard Normal Linear VaR (Baseline)
z_01 = norm.ppf(conf_level)
normal_var = -((z_01 * vol_ann * np.sqrt(horizon/250)) + (mu_ann * horizon/250))

# 2. Cornish-Fisher Adjusted VaR
cf_var = calculate_cornish_fisher_var(
    alpha=conf_level, mu_annual=mu_ann, vol_annual=vol_ann, 
    skewness=skew, excess_kurtosis=exc_kurtosis, h_days=horizon
)

print("--- Example IV.3.4: Cornish-Fisher VaR ---")
print(f"Normal Linear 1% 10-day VaR: {normal_var:.2%}")
print(f"Cornish-Fisher 1% 10-day VaR: {cf_var:.2%}")
print(f"Difference due to Skew & Kurtosis: {cf_var - normal_var:.2%}")