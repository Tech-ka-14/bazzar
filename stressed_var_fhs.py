import numpy as np

def simulate_stressed_fhs_garch(
    historical_standardized_residuals: np.ndarray,
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
    using Filtered Historical Simulation (bootstrapping empirical residuals).
    """
    shock_var_daily = (shock_vol_annual / np.sqrt(250))**2
    liquidation_weights = np.array([(h_days - t + 1) / h_days for t in range(1, h_days + 1)])
    
    total_simulated_returns = np.zeros(n_simulations)
    n_historical_obs = len(historical_standardized_residuals)
    
    for i in range(n_simulations):
        current_var = shock_var_daily
        prev_return = shock_return
        path_returns = np.zeros(h_days)
        
        # Bootstrap: Draw h random indices with replacement from historical data
        random_indices = np.random.randint(0, n_historical_obs, h_days)
        z_shocks = historical_standardized_residuals[random_indices]
        
        for t in range(h_days):
            current_var = omega + alpha * (prev_return - lambda_asym)**2 + beta * current_var
            current_vol = np.sqrt(current_var)
            
            # Generate today's simulated return using the empirical standardized residual
            current_return = current_vol * z_shocks[t]
            path_returns[t] = current_return
            prev_return = current_return
            
        total_simulated_returns[i] = np.sum(path_returns * liquidation_weights)
        
    return total_simulated_returns