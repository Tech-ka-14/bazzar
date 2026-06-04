import numpy as np
from scipy.stats import norm

def calculate_dollar_beta(positions: list, betas: list):
    """
    Calculates the net portfolio dollar beta given a list of position values and their respective betas.
    
    Parameters:
    positions (list): Monetary value invested in each asset.
    betas (list): The sensitivity (beta) of each asset with respect to the risk factor.
    
    Returns:
    float: The net portfolio dollar beta.
    """
    return sum(pos * beta for pos, beta in zip(positions, betas))

def calculate_equity_var(dollar_beta: float, mu_annual: float, sigma_annual: float, 
                         horizon_days: int, confidence_level: float, days_in_year: int = 250):
    """
    Calculates the Normal Linear Equity VaR (Systematic VaR) for a mapped portfolio.
    
    Parameters:
    dollar_beta (float): The net portfolio beta expressed in monetary terms.
    mu_annual (float): Expected annual excess return of the risk factor (market index).
    sigma_annual (float): Annual volatility of the risk factor.
    horizon_days (int): The VaR risk horizon in days (h).
    confidence_level (float): The confidence level (e.g., 0.99 for 1% significance).
    days_in_year (int): Trading days in a year to scale returns/volatility.
    
    Returns:
    float: The Equity VaR in monetary terms.
    """
    # Scale annual expectations and volatility to the h-day risk horizon
    time_fraction = horizon_days / days_in_year
    mu_h = mu_annual * time_fraction
    sigma_h = sigma_annual * np.sqrt(time_fraction)
    
    # Calculate the standard normal critical value
    alpha = 1.0 - confidence_level
    critical_value = norm.ppf(1 - alpha)
    
    # Apply Formula IV.1.26: Equity VaR = Beta * (Z * sigma_h - mu_h)
    equity_var = dollar_beta * ((critical_value * sigma_h) - mu_h)
    
    return equity_var

# Example IV.1.7: Equity VaR for a Two-Stock Portfolio
# Portfolio Details
positions_millions = [1.0, 2.0]  # $1m and $2m invested
asset_betas = [1.2, 0.8]

# Risk Factor (Market Index) Details
market_mu_annual = 0.05       # 5% annual expected excess return
market_sigma_annual = 0.20    # 20% annual volatility
risk_horizon = 10             # 10-day VaR
conf_level = 0.99             # 1% Significance Level

# 1. Calculate Dollar Beta
net_dollar_beta = calculate_dollar_beta(positions_millions, asset_betas)

# 2. Calculate Systematic Equity VaR
systematic_var = calculate_equity_var(net_dollar_beta, market_mu_annual, 
                                      market_sigma_annual, risk_horizon, conf_level)

print(f"Net Portfolio Dollar Beta: ${net_dollar_beta:.2f} million")
print(f"1% 10-day Equity VaR: ${systematic_var * 1_000_000:,.0f}")