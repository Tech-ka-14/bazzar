import numpy as np

def simulate_agarch_returns(z_matrix: np.ndarray, initial_vol: float, initial_return: float, 
                            omega: float, alpha: float, beta: float, lambda_asym: float) -> np.ndarray:
    """
    Simulates daily log returns incorporating A-GARCH volatility and mean reversion.
    z_matrix shape: (n_simulations, h_days) containing standard normal draws.
    """
    n_simulations, h_days = z_matrix.shape
    simulated_returns = np.zeros((n_simulations, h_days))
    
    # Initialize variance for the first step
    current_variance = np.full(n_simulations, initial_vol**2)
    previous_return = np.full(n_simulations, initial_return)
    
    for t in range(h_days):
        # Update variance using the A-GARCH recurrence
        # Note: the text uses lambda for the asymmetry shift here, separate from EWMA's lambda
        shock_term = (previous_return - lambda_asym)**2
        current_variance = omega + (alpha * shock_term) + (beta * current_variance)
        current_vol = np.sqrt(current_variance)
        
        # Simulate today's return
        current_return = current_vol * z_matrix[:, t]
        simulated_returns[:, t] = current_return
        
        # Prepare for the next step
        previous_return = current_return
        
    return simulated_returns