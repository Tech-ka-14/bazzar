import pandas as pd
import numpy as np
from scipy.stats import norm

def calculate_ewma_specific_var(portfolio_returns: pd.Series, factor_returns: pd.Series, 
                                lam: float = 0.95, alpha: float = 0.01, h_days: int = 10):
    """
    Calculates the highly risk-sensitive Specific VaR using EWMA for beta 
    and residual variance (Equation IV.2.48).
    """
    # 1. Calculate EWMA Variance of the Factor and EWMA Covariance
    ewma_var_x = factor_returns.ewm(alpha=1-lam, adjust=False).var()
    ewma_cov_xy = factor_returns.ewm(alpha=1-lam, adjust=False).cov(portfolio_returns)
    
    # 2. Calculate dynamic EWMA Beta
    ewma_beta = ewma_cov_xy / ewma_var_x
    
    # 3. Calculate dynamic residuals: e_t = Y_t - (beta_t * X_t)
    residuals = portfolio_returns - (ewma_beta * factor_returns)
    
    # 4. Calculate EWMA Volatility of the residuals (sigma^e_t)
    ewma_residual_vol = np.sqrt(residuals.ewm(alpha=1-lam, adjust=False).var())
    
    # 5. Calculate Specific VaR for the most recent observation
    latest_residual_vol = ewma_residual_vol.iloc[-1]
    critical_val = norm.ppf(1 - alpha)
    
    specific_var_h = critical_val * np.sqrt(h_days) * latest_residual_vol
    
    return specific_var_h, ewma_beta.iloc[-1]

# Simulated market data (100 days)
np.random.seed(42)
market_returns = pd.Series(np.random.normal(0, 0.01, 100))
# Portfolio has beta of ~1.2 plus some idiosyncratic noise
port_returns = pd.Series(1.2 * market_returns + np.random.normal(0, 0.005, 100))

# Execute EWMA Specific VaR calculation
spec_var, current_beta = calculate_ewma_specific_var(
    port_returns, market_returns, lam=0.95, alpha=0.01, h_days=10
)

print(f"Current EWMA Beta Estimate: {current_beta:.4f}")
print(f"1% 10-day EWMA Specific VaR (Percentage): {spec_var:.4%}")