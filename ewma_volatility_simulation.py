import numpy as np

def simulate_ewma_returns(z_matrix: np.ndarray, initial_vol: float, initial_return: float, lambda_param: float) -> np.ndarray:
    """
    Simulates daily log returns incorporating EWMA volatility clustering.
    z_matrix shape: (n_simulations, h_days) containing standard normal draws.
    """
    n_simulations, h_days = z_matrix.shape
    simulated_returns = np.zeros((n_simulations, h_days))
    
    # Initialize variance for the first step
    current_variance = np.full(n_simulations, initial_vol**2)
    previous_return = np.full(n_simulations, initial_return)
    
    for t in range(h_days):
        # Update variance using the EWMA recurrence
        current_variance = (1 - lambda_param) * (previous_return**2) + lambda_param * current_variance
        current_vol = np.sqrt(current_variance)
        
        # Simulate today's return
        current_return = current_vol * z_matrix[:, t]
        simulated_returns[:, t] = current_return
        
        # Prepare for the next step
        previous_return = current_return
        
    return simulated_returns