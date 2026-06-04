import numpy as np

def calculate_commodity_historical_var(ho_contracts: np.ndarray, ho_spread_changes: np.ndarray,
                                       ul_contracts: np.ndarray, ul_spread_changes: np.ndarray,
                                       multiplier: float = 1000.0, alpha: float = 0.01, 
                                       horizon_days: int = 10) -> tuple:
    """
    Calculates Stand-Alone and Total Historical VaR for a Commodity Futures portfolio.
    
    Parameters:
    ho_contracts, ul_contracts (np.ndarray): Fixed number of contracts at each maturity.
    ho_spread_changes, ul_spread_changes (np.ndarray): Historical daily absolute spread changes.
    multiplier (float): Contract size multiplier (e.g., 1000 barrels).
    
    Returns:
    tuple: (Heating Oil Stand-Alone VaR, Unleaded Stand-Alone VaR, Total Aggregated VaR)
    """
    
    # 1. Simulate unscaled daily P&L per component (Contracts * Absolute Change)
    pnl_ho = np.dot(ho_spread_changes, ho_contracts)
    pnl_ul = np.dot(ul_spread_changes, ul_contracts)
    
    # Total combined unscaled daily P&L
    pnl_total = pnl_ho + pnl_ul
    
    # 2. Extract empirical quantiles
    quant_ho = np.quantile(pnl_ho, alpha, method='linear')
    quant_ul = np.quantile(pnl_ul, alpha, method='linear')
    quant_total = np.quantile(pnl_total, alpha, method='linear')
    
    # 3. Apply Multiplier (-1000) and scale by square-root of time
    time_scale = np.sqrt(horizon_days)
    
    var_ho = -quant_ho * multiplier * time_scale
    var_ul = -quant_ul * multiplier * time_scale
    var_total = -quant_total * multiplier * time_scale
    
    return var_ho, var_ul, var_total

# Conceptual Setup: 6 maturities for Heating Oil (HO) and 6 for Unleaded (UL)
mock_ho_contracts = np.array([-50, -20, 10, 30, 40, 50])
mock_ul_contracts = np.array([100, 50, 20, -10, -30, -50])

np.random.seed(100)
# Mock historical changes (highly positively correlated spreads)
market_factor = np.random.normal(0, 0.02, (1000, 1))
mock_ho_changes = market_factor + np.random.normal(0, 0.005, (1000, 6))
mock_ul_changes = market_factor * 1.2 + np.random.normal(0, 0.005, (1000, 6))

va_ho, va_ul, va_total = calculate_commodity_historical_var(
    mock_ho_contracts, mock_ho_changes,
    mock_ul_contracts, mock_ul_changes
)

print("--- Crack Spread Historical VaR Decomposition ---")
print(f"Heating Oil (HO) Stand-Alone VaR: ${va_ho:,.0f}")
print(f"Unleaded Gas (UL) Stand-Alone VaR: ${va_ul:,.0f}")
print(f"Sum of Stand-Alone VaRs: ${va_ho + va_ul:,.0f}")
print("-" * 40)
print(f"Total Portfolio VaR (Diversified): ${va_total:,.0f}")