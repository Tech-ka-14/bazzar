import numpy as np

def calculate_regulatory_market_capital(simulated_daily_returns: np.ndarray, portfolio_value: float) -> float:
    """
    Calculates the minimum Regulatory Capital using the Basel Internal Model approach.
    Strictly requires a 1% confidence level over a 10-day horizon.
    """
    # Regulatory parameters
    alpha = 0.01
    h_days = 10
    
    # Scale daily simulated returns to h-day returns (Assuming i.i.d for this basic example)
    # In practice, multi-step simulation (as built previously) is preferred.
    h_day_returns = simulated_daily_returns * np.sqrt(h_days)
    
    # Calculate 1% VaR as a percentage
    var_percent = -np.quantile(h_day_returns, alpha)
    
    # Capital required is the Value at Risk in absolute terms
    regulatory_capital = var_percent * portfolio_value
    return regulatory_capital

def calculate_economic_capital(simulated_horizon_returns: np.ndarray, portfolio_value: float, 
                               alpha: float, use_etl: bool = True) -> float:
    """
    Calculates the internal Economic Capital for solvency and credit-rating purposes.
    Allows for flexible horizons, confidence levels, and the use of Expected Tail Loss (ETL).
    """
    var_percent = -np.quantile(simulated_horizon_returns, alpha)
    
    if use_etl:
        # Calculate Expected Tail Loss (Average of losses exceeding VaR)
        tail_losses = simulated_horizon_returns[simulated_horizon_returns < -var_percent]
        etl_percent = -np.mean(tail_losses) if len(tail_losses) > 0 else var_percent
        economic_capital = etl_percent * portfolio_value
    else:
        economic_capital = var_percent * portfolio_value
        
    return economic_capital

# Example Usage:
# Assume we have 10,000 simulated daily returns for a $100M portfolio
simulated_returns = np.random.normal(0.0005, 0.015, 10000)
portfolio_value = 100_000_000

# 1. Bank computes regulatory requirement (Strict 1% 10-Day VaR)
reg_capital = calculate_regulatory_market_capital(simulated_returns, portfolio_value)

# 2. Bank computes its own internal Economic Capital using a stricter 0.1% ETL over 1-year (250 days)
# (Simulating an annualized horizon based on daily data for demonstration)
annualized_returns = simulated_returns * np.sqrt(250)
econ_capital = calculate_economic_capital(annualized_returns, portfolio_value, alpha=0.001, use_etl=True)