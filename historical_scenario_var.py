import numpy as np
import scipy.stats as stats

def calculate_normal_scenario_var(mean: float, std_dev: float, alpha: float) -> float:
    """
    Calculates the Scenario VaR assuming the crisis distribution is Normal.
    """
    z_score = stats.norm.ppf(1 - alpha)
    # VaR is typically expressed as a positive loss percentage
    var = (z_score * std_dev) - mean
    return var

def calculate_cornish_fisher_scenario_var(mean: float, std_dev: float, skewness: float, excess_kurtosis: float, alpha: float) -> float:
    """
    Calculates the Scenario VaR using a Cornish-Fisher expansion to account 
    for the extreme skewness and kurtosis present in the crisis scenario.
    """
    z = stats.norm.ppf(1 - alpha)
    
    # Cornish-Fisher expansion adjustment
    z_cf = z + (1/6) * (z**2 - 1) * skewness \
           + (1/24) * (z**3 - 3*z) * excess_kurtosis \
           - (1/36) * (2*z**3 - 5*z) * (skewness**2)
           
    var = (z_cf * std_dev) - mean
    return var

# Example IV.7.1: 1987 Global Equity Crash Scenario
crash_mean = -0.0121  # -1.21%
crash_std = 0.0394    # 3.94%
crash_skew = -0.3202
crash_kurt = 1.6139

# 99% Confidence (alpha = 0.01)
normal_var_99 = calculate_normal_scenario_var(crash_mean, crash_std, 0.01)
cf_var_99 = calculate_cornish_fisher_scenario_var(crash_mean, crash_std, crash_skew, crash_kurt, 0.01)