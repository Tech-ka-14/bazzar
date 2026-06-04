import numpy as np
from scipy.stats import norm

def calculate_normal_var(mu: float, sigma: float, confidence_level: float, portfolio_value: float = None):
    """
    Calculates the analytical Value at Risk (VaR) assuming normally distributed returns.
    
    Parameters:
    mu (float): Expected return (mean) over the risk horizon.
    sigma (float): Volatility (standard deviation) over the risk horizon.
    confidence_level (float): The confidence level (e.g., 0.99 for 99% VaR).
    portfolio_value (float, optional): Current value of the portfolio. If provided, returns monetary VaR.
    
    Returns:
    float: VaR as a percentage, or monetary VaR if portfolio_value is provided.
    """
    # Calculate the significance level alpha
    alpha = 1.0 - confidence_level
    
    # Calculate the inverse of the standard normal CDF
    critical_value = norm.ppf(1 - alpha)
    
    # Calculate VaR as a percentage (Formula IV.1.15)
    var_percentage = (critical_value * sigma) - mu
    
    # Return monetary VaR if portfolio value is specified (Formula IV.1.16)
    if portfolio_value is not None:
        return var_percentage * portfolio_value
        
    return var_percentage

# Example IV.1.4: 10% VaR over 1-year horizon
mu_annual = 0.05
sigma_annual = 0.12
portfolio_val = 2_000_000
conf_level = 0.90 # Represents alpha = 0.10

var_pct = calculate_normal_var(mu_annual, sigma_annual, conf_level)
var_value = calculate_normal_var(mu_annual, sigma_annual, conf_level, portfolio_val)

print(f"10% 1-year VaR (Percentage): {var_pct:.4%}")
print(f"10% 1-year VaR (Value): ${var_value:,.2f}")