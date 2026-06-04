import numpy as np

def calculate_historical_pv01_var(pv01_vector: np.ndarray, 
                                  rate_changes_historical: np.ndarray, 
                                  alpha: float = 0.01, 
                                  horizon_days: int = 10) -> float:
    """
    Calculates Historical VaR for an interest-rate sensitive portfolio 
    using the PV01 cash-flow mapping. (Equations IV.3.12 & IV.3.13)
    
    Parameters:
    pv01_vector (np.ndarray): Array of PV01s for each maturity vertex (n x 1).
    rate_changes_historical (np.ndarray): Historical daily rate changes in basis points (T days x n vertices).
    alpha (float): Significance level (e.g., 0.01 for 1% VaR).
    horizon_days (int): Holding period for scaling the 1-day VaR.
    
    Returns:
    float: The scaled Historical VaR in nominal terms.
    """
    # 1. Generate the simulated historical P&L series using Equation IV.3.13
    # P&L_t = - (p' * delta_r_t)
    simulated_pnl = -np.dot(rate_changes_historical, pv01_vector)
    
    # 2. Extract the alpha quantile from the empirical distribution
    empirical_quantile = np.quantile(simulated_pnl, alpha, method='linear')
    
    # 3. Calculate 1-day VaR (Negative of the loss quantile)
    var_1_day = -empirical_quantile
    
    # 4. Scale to the specified risk horizon
    var_h_day = var_1_day * np.sqrt(horizon_days)
    
    return var_h_day

# Conceptual Setup: 3 maturity vertices over 1000 days of history
mock_pv01 = np.array([500.0, -1000.0, 2000.0]) # Nominal dollar sensitivities
np.random.seed(42)
mock_historical_rates = np.random.normal(0, 5, (1000, 3)) # 5 basis point daily volatility

hist_var_10d = calculate_historical_pv01_var(mock_pv01, mock_historical_rates)
print(f"1% 10-Day Historical PV01 VaR: ${hist_var_10d:,.2f}")