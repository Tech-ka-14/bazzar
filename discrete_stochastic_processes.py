import numpy as np

def simulate_ar1_process(alpha, rho, volatility, steps, initial_value=0):
    """
    Simulates a discrete-time First Order Autoregression AR(1) process.
    If |rho| < 1, the process is stationary.
    If rho == 1, the process is a Random Walk.
    """
    x = np.zeros(steps)
    x[0] = initial_value
    
    # Generate standard normal independent increments (white noise)
    z = np.random.standard_normal(steps)
    
    for t in range(1, steps):
        epsilon_t = volatility * z[t]
        x[t] = alpha + (rho * x[t-1]) + epsilon_t
        
    return x

def calculate_ar1_theoretical_moments(alpha, rho, volatility):
    """
    Calculates the finite expected value and variance of a stationary AR(1) process.
    Returns None if the process is non-stationary (|rho| >= 1).
    """
    if abs(rho) >= 1:
        return None, None # Expectation and variance are infinite
        
    expected_value = alpha / (1 - rho)
    variance = (volatility ** 2) / (1 - (rho ** 2))
    
    return expected_value, variance