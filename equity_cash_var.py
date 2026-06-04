import numpy as np
from scipy.stats import norm

def calculate_equity_cash_var(weights: np.ndarray, cov_matrix_h: np.ndarray, 
                              expected_returns_h: np.ndarray, portfolio_value: float, 
                              alpha: float = 0.01) -> tuple:
    """
    Calculates the Normal Linear VaR for a cash equity portfolio, both with 
    and without the expected drift adjustment (Equation IV.2.44).
    """
    # 1. Calculate Portfolio Volatility (sqrt(w' * V * w))
    portfolio_variance = weights.T @ cov_matrix_h @ weights
    portfolio_volatility = np.sqrt(portfolio_variance)
    
    # 2. Calculate the Expected Portfolio Return (w' * E(x))
    expected_portfolio_return = weights.T @ expected_returns_h
    
    # 3. Base VaR (Zero Mean Assumption)
    critical_value = norm.ppf(1 - alpha)
    var_zero_mean_pct = critical_value * portfolio_volatility
    var_zero_mean_val = var_zero_mean_pct * portfolio_value
    
    # 4. Drift Adjusted VaR
    var_adjusted_pct = var_zero_mean_pct - expected_portfolio_return
    var_adjusted_val = var_adjusted_pct * portfolio_value
    
    return var_zero_mean_val, var_adjusted_val

# Example IV.2.11: VaR for Cash Equity Positions (10-day horizon)
# Positions in millions of Euros
positions = np.array([4.0, -5.0, 1.0])
total_portfolio_value = np.sum(np.abs(positions)) # Gross Exposure basis

# 10-day Expected Returns
expected_ret_10d = np.array([0.004, 0.0008, 0.002])

# 10-day Covariance Matrix
cov_10d = np.array([
    [0.0016,  0.00064, 0.0006],
    [0.00064, 0.0004,  0.00018],
    [0.0006,  0.00018, 0.0009]
])

var_base, var_adj = calculate_equity_cash_var(
    positions, cov_10d, expected_ret_10d, total_portfolio_value=1.0, alpha=0.01
)

print(f"1% 10-day VaR (Zero Drift): €{var_base:,.0f}")
print(f"1% 10-day VaR (Drift Adjusted): €{var_adj:,.0f}")