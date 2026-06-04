import numpy as np

def calculate_empirical_historical_var(historical_returns: np.ndarray, portfolio_value: float, confidence_level: float):
    """
    Calculates Historical Simulation VaR using empirical quantiles and interpolation.
    
    Parameters:
    historical_returns (np.ndarray): An array of historically simulated h-day returns.
    portfolio_value (float): The current nominal value of the portfolio.
    confidence_level (float): The target confidence level (e.g., 0.99 for 1% VaR).
    
    Returns:
    tuple: (VaR percentage, VaR in value terms)
    """
    alpha = 1.0 - confidence_level
    
    # Sort the returns to build the empirical cumulative distribution
    sorted_returns = np.sort(historical_returns)
    
    # Find the alpha quantile. 
    # By default, numpy's quantile uses linear interpolation between discrete historical nodes.
    var_percentile = np.quantile(sorted_returns, alpha, method='linear')
    
    # VaR is strictly defined as the negative of the loss quantile
    var_percentage = -var_percentile
    var_value = var_percentage * portfolio_value
    
    return var_percentage, var_value

# Mock dataset representing a 1000-day historical simulation
np.random.seed(42)
# Creating a fat-tailed distribution (Student-t) to emphasize non-normality
historical_sim_returns = np.random.standard_t(df=4, size=1000) * 0.015 

current_portfolio_value = 1_000_000
conf = 0.99 # 99% Confidence (1% VaR)

var_pct, var_val = calculate_empirical_historical_var(historical_sim_returns, current_portfolio_value, conf)

print("--- Historical Simulation VaR ---")
print(f"Number of Simulated Scenarios: {len(historical_sim_returns)}")
print(f"1% Historical VaR (Percentage): {var_pct:.4%}")
print(f"1% Historical VaR (Value): ${var_val:,.2f}")