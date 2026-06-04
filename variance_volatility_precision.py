import numpy as np
import scipy.stats as stats

def variance_volatility_metrics(variance_estimate, T, confidence_level=0.95):
    """
    Calculates confidence intervals and standard errors for 
    equally weighted variance and volatility estimates.
    """
    alpha = 1 - confidence_level
    
    # 1. Confidence Interval for Variance
    # Obtain the critical chi-squared values
    chi2_lower = stats.chi2.ppf(alpha / 2, T)
    chi2_upper = stats.chi2.ppf(1 - alpha / 2, T)
    
    # Calculate bounds
    var_lower_bound = (T * variance_estimate) / chi2_upper
    var_upper_bound = (T * variance_estimate) / chi2_lower
    
    # 2. Confidence Interval for Volatility (Square Root Transformation)
    volatility_estimate = np.sqrt(variance_estimate)
    vol_lower_bound = np.sqrt(var_lower_bound)
    vol_upper_bound = np.sqrt(var_upper_bound)
    
    # 3. Standard Errors
    # Percentage standard error for variance = sqrt(2/T)
    var_pct_se = np.sqrt(2 / T)
    var_se = var_pct_se * variance_estimate
    
    # Percentage standard error for volatility approx = sqrt(1 / (2T))
    vol_pct_se = np.sqrt(1 / (2 * T))
    vol_se = vol_pct_se * volatility_estimate
    
    return {
        "Variance Estimate": variance_estimate,
        "Variance CI": (var_lower_bound, var_upper_bound),
        "Variance Std Error": var_se,
        "Volatility Estimate": volatility_estimate,
        "Volatility CI": (vol_lower_bound, vol_upper_bound),
        "Volatility Std Error": vol_se
    }

# Example implementation based on text parameters
metrics = variance_volatility_metrics(variance_estimate=0.04, T=30, confidence_level=0.95)