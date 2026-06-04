import numpy as np

def calculate_ewma_adjusted_pnl(pnl_series: np.ndarray, lambda_ewma: float = 0.90) -> np.ndarray:
    """
    Applies EWMA to extract the volatility of the P&L series and scales 
    historical P&L to reflect the most recent 'current' volatility state.
    """
    n = len(pnl_series)
    ewma_var = np.zeros(n)
    
    # Initialize with the sample variance
    ewma_var[0] = np.var(pnl_series)
    
    # Recursive EWMA variance calculation
    for t in range(1, n):
        ewma_var[t] = (1 - lambda_ewma) * (pnl_series[t-1]**2) + (lambda_ewma * ewma_var[t-1])
        
    ewma_vol = np.sqrt(ewma_var)
    current_vol = ewma_vol[-1] # The most recent volatility state
    
    # Scale historical P&L scenarios by the ratio of current vol to historical vol
    adjusted_pnl_series = pnl_series * (current_vol / ewma_vol)
    
    return adjusted_pnl_series

# Example Implementation using the previous mock data
raw_simulated_pnl = -np.dot(mock_historical_rates, mock_pv01)

# Apply EWMA adjustment (using lambda 0.90 as mentioned in the case study)
adjusted_pnl = calculate_ewma_adjusted_pnl(raw_simulated_pnl, lambda_ewma=0.90)

# Calculate unadjusted vs adjusted VaR
unadjusted_var = -np.quantile(raw_simulated_pnl, 0.01) * np.sqrt(10)
adjusted_var = -np.quantile(adjusted_pnl, 0.01) * np.sqrt(10)

print(f"Unadjusted 1% 10-Day VaR: ${unadjusted_var:,.2f}")
print(f"EWMA Adjusted 1% 10-Day VaR: ${adjusted_var:,.2f}")