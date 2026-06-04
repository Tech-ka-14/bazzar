import numpy as np

def simulate_gbm_paths(S0, drift, volatility, T, steps, num_paths=1):
    """
    Simulates asset price paths following Geometric Brownian Motion.
    
    Parameters:
    S0 (float): Current asset price.
    drift (float): The expected annualized return (or risk-free rate).
    volatility (float): The annualized standard deviation of returns.
    T (float): Total time horizon in years.
    steps (int): Number of discrete time steps.
    num_paths (int): Number of independent price paths to simulate.
    
    Returns:
    numpy.ndarray: An array of shape (steps + 1, num_paths) containing the simulated prices.
    """
    dt = T / steps
    
    # Calculate the deterministic drift term
    alpha = (drift - 0.5 * volatility**2) * dt
    
    # Calculate the standard deviation for the discrete time step
    sigma_sq_dt = volatility * np.sqrt(dt)
    
    # Generate random standard normal draws for all steps and paths
    Z = np.random.standard_normal((steps, num_paths))
    
    # Calculate the log returns for each step
    log_returns = alpha + sigma_sq_dt * Z
    
    # Initialize the array to hold the price paths
    price_paths = np.zeros((steps + 1, num_paths))
    price_paths[0] = S0
    
    # Accumulate the log returns and exponentiate to get the exact price paths
    price_paths[1:] = S0 * np.exp(np.cumsum(log_returns, axis=0))
    
    return price_paths

if __name__ == "__main__":
    # Example replicating the text's scenario: 1 year, daily steps, 5% drift, 20% vol
    current_price = 100.0
    risk_free_rate = 0.05
    annual_vol = 0.20
    time_horizon = 1.0
    trading_days = 365
    
    np.random.seed(42) # For reproducibility
    simulated_paths = simulate_gbm_paths(
        S0=current_price, 
        drift=risk_free_rate, 
        volatility=annual_vol, 
        T=time_horizon, 
        steps=trading_days, 
        num_paths=4 # Simulating 4 independent paths
    )
    
    print("--- Geometric Brownian Motion Simulation ---")
    print(f"Initial Price: {simulated_paths[0, 0]}")
    print("Terminal Prices (Day 365) for 4 paths:")
    print(np.round(simulated_paths[-1, :], 2))