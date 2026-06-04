import numpy as np
from scipy.stats import norm

def calculate_ewma_var(current_ewma_vol_daily: float, portfolio_value: float, 
                       alpha: float = 0.01, horizon_days: int = 10) -> float:
    """
    Calculates the short-term EWMA Normal Linear VaR (Equation IV.2.82).
    """
    # Standard normal critical value
    critical_value = norm.ppf(1 - alpha)
    
    # Scale daily volatility to h-day horizon
    volatility_h = current_ewma_vol_daily * np.sqrt(horizon_days)
    
    # Calculate VaR
    var_estimate = critical_value * volatility_h * portfolio_value
    
    return var_estimate

# Using the RiskMetrics framework for a $1,000,000 portfolio
current_daily_volatility = np.sqrt(0.00015) # Example derived from an EWMA process
confidence_lvl = 0.01 # 1% VaR
horizon = 10 # 10-Day VaR

ewma_var = calculate_ewma_var(
    current_ewma_vol_daily=current_daily_volatility, 
    portfolio_value=1_000_000, 
    alpha=confidence_lvl, 
    horizon_days=horizon
)

print(f"1% 10-Day EWMA VaR: ${ewma_var:,.0f}")