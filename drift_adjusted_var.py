import numpy as np
from scipy.stats import norm

def calculate_drift_adjusted_var(mean_return_annual: float, vol_annual: float, risk_free_rate: float, 
                                 horizon_months: float, confidence_level: float):
    """
    Calculates the VaR accounting for non-zero expected excess returns (drift adjustment).
    Matches the calculations shown in Table IV.1.3.
    
    Parameters:
    mean_return_annual (float): Expected annual return of the portfolio.
    vol_annual (float): Annual volatility of the portfolio.
    risk_free_rate (float): Annual risk-free interest rate.
    horizon_months (float): Risk horizon in months.
    confidence_level (float): Confidence level for the VaR.
    
    Returns:
    tuple: (Non-adjusted VaR, Drift-Adjusted VaR, Difference)
    """
    # Convert annual parameters to the specific risk horizon
    time_fraction = horizon_months / 12.0
    
    mean_h = mean_return_annual * time_fraction
    vol_h = vol_annual * np.sqrt(time_fraction)
    
    # Calculate discount factor based on continuous risk-free rate
    discount_factor = np.exp(-risk_free_rate * time_fraction)
    
    # Discounted statistics
    discounted_mean = mean_h * discount_factor
    discounted_vol = vol_h * discount_factor
    
    alpha = 1.0 - confidence_level
    z_score = norm.ppf(alpha)
    
    # VaR Assuming Zero Mean Excess Return (Base VaR)
    var_zero_mean = - (z_score * discounted_vol)
    
    # Drift Adjusted VaR (incorporating the expected mean)
    lower_quantile = (z_score * discounted_vol) + discounted_mean
    var_adjusted = -lower_quantile
    
    difference = var_zero_mean - var_adjusted
    
    return var_zero_mean, var_adjusted, difference

# Example IV.1.6: 12-month horizon with 10% expected return and 5% risk free rate
horizon_m = 12.0
mean_ret = 0.10
vol = 0.20
rf_rate = 0.05
conf = 0.99

var_base, var_adj, diff = calculate_drift_adjusted_var(mean_ret, vol, rf_rate, horizon_m, conf)

print(f"Risk Horizon: {horizon_m} months")
print(f"1% VaR (Zero Mean): {var_base:.4%}")
print(f"1% VaR (Drift Adjusted): {var_adj:.4%}")
print(f"Reduction in VaR (Difference): {diff:.4%}")