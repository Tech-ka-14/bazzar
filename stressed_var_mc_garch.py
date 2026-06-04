import numpy as np

def simulate_stressed_mc_garch(
    n_simulations: int, 
    h_days: int, 
    shock_return: float, 
    shock_vol_annual: float,
    omega: float, 
    alpha: float, 
    beta: float, 
    lambda_asym: float
) -> np.ndarray:
    """
    Simulates total returns for a gradually liquidated portfolio under stressed conditions
    using a Monte Carlo Asymmetric GARCH model.
    """
    # Convert annualized volatility shock to daily variance
    shock_var_daily = (shock_vol_annual / np.sqrt(250))**2
    
    # Calculate uniform liquidation weights: [1.0, 0.9, 0.8, ..., 0.1] for h=10
    liquidation_weights = np.array([(h_days - t + 1) / h_days for t in range(1, h_days + 1)])
    
    total_simulated_returns = np.zeros(n_simulations)
    
    for i in range(n_simulations):
        current_var = shock_var_daily
        prev_return = shock_return
        path_returns = np.zeros(h_days)
        
        # Simulate standard normal shocks
        z_shocks = np.random.standard_normal(h_days)
        
        for t in range(h_days):
            # Update Asymmetric GARCH variance based on the PREVIOUS day's shock
            current_var = omega + alpha * (prev_return - lambda_asym)**2 + beta * current_var
            current_vol = np.sqrt(current_var)
            
            # Generate today's simulated return
            current_return = current_vol * z_shocks[t]
            path_returns[t] = current_return
            
            # Prepare for the next step
            prev_return = current_return
            
        # Calculate total return applying the liquidation weights
        total_simulated_returns[i] = np.sum(path_returns * liquidation_weights)
        
    return total_simulated_returns

# Example IV.7.19 Parameters
# Simulated 10-day Stressed VaR with uniform liquidation
stressed_returns = simulate_stressed_mc_garch(
    n_simulations=10000, 
    h_days=10, 
    shock_return=-0.10,      # -10% shock
    shock_vol_annual=0.60,   # 60% annualized volatility
    omega=0.000002,          # Example GARCH params (replace with actual from Table IV.3.5)
    alpha=0.05,
    beta=0.90,
    lambda_asym=0.0         
)

# Calculate 0.1% VaR (Result should be ~32.49% as per Table IV.7.11)
stressed_var_99_9 = -np.quantile(stressed_returns, 0.001)