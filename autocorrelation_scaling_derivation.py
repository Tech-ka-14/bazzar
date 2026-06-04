import numpy as np
from scipy.stats import norm

def calculate_adjusted_time_horizon(h: int, rho: float) -> float:
    """
    Analytically calculates the adjusted time horizon (h_tilde) for a first-order 
    autoregressive (AR1) return process using Equation IV.2.10.
    """
    if rho == 0:
        return float(h)
    
    # Calculate the adjustment factor (the second term in IV.2.10)
    term_1 = (h - 1) * (1 - rho)
    term_2 = rho * (1 - rho**(h - 1))
    
    adjustment_factor = 2 * (rho / (1 - rho)**2) * (term_1 - term_2)
    h_tilde = h + adjustment_factor
    
    return h_tilde

def calculate_autocorrelated_var(mu_1: float, sigma_1: float, h: int, rho: float, alpha: float) -> float:
    """
    Calculates the scaled Normal Linear VaR (Equation IV.2.11).
    """
    h_tilde = calculate_adjusted_time_horizon(h, rho)
    
    critical_value = norm.ppf(1 - alpha)
    var_h = (np.sqrt(h_tilde) * critical_value * sigma_1) - (h * mu_1)
    
    return var_h, h_tilde

# Example IV.2.1: Adjusting Normal Linear VaR for Autocorrelation
mu_daily = 0.0001    # 0.01% daily mean
sigma_daily = 0.01   # 1% daily volatility
rho_ar1 = 0.2        # Autocorrelation
significance = 0.01  # 1% VaR

print("--- Example IV.2.1: h = 250 days ---")
var_250, h_tilde_250 = calculate_autocorrelated_var(mu_daily, sigma_daily, 250, rho_ar1, significance)
print(f"Adjustment Factor added to h: {h_tilde_250 - 250:.3f}")
print(f"Adjusted Horizon (h_tilde): {h_tilde_250:.3f}")
print(f"Annual Volatility: {sigma_daily * np.sqrt(h_tilde_250):.2%}")

print("\n--- Example IV.2.1: h = 10 days ---")
var_10, h_tilde_10 = calculate_autocorrelated_var(mu_daily, sigma_daily, 10, rho_ar1, significance)
print(f"Adjustment Factor added to h: {h_tilde_10 - 10:.3f}")
print(f"1% 10-day VaR (Autocorrelated): {var_10:.2%}")