import numpy as np

def simulate_geometric_brownian_motion(mu, sigma, s0, dt, steps):
    """
    Simulates an asset price path using Geometric Brownian Motion (GBM).
    Uses the exact discrete time equivalent derived from Ito's Lemma:
    Delta ln P_t = (mu - 0.5 * sigma^2)*dt + sigma * sqrt(dt) * Z
    """
    prices = np.zeros(steps)
    prices[0] = s0
    
    # Drift adjustment for log returns as per the text's discretization
    alpha = mu - (0.5 * sigma**2)
    
    # Generate standard normal variables
    z = np.random.standard_normal(steps)
    
    for t in range(1, steps):
        # Calculate the log return
        epsilon_t = sigma * np.sqrt(dt) * z[t]
        log_return = (alpha * dt) + epsilon_t
        
        # Exponential transformation to get the price
        prices[t] = prices[t-1] * np.exp(log_return)
        
    return prices

def simulate_mean_reverting_process(phi, theta, sigma, x0, dt, steps):
    """
    Simulates a continuous stationary process: dX(t) = phi*(theta - X(t))dt + sigma*dB(t)
    phi: rate of mean reversion
    theta: long term value
    """
    x = np.zeros(steps)
    x[0] = x0
    
    z = np.random.standard_normal(steps)
    
    for t in range(1, steps):
        # Discretization of the mean-reverting SDE
        deterministic_part = phi * (theta - x[t-1]) * dt
        stochastic_part = sigma * np.sqrt(dt) * z[t]
        
        x[t] = x[t-1] + deterministic_part + stochastic_part
        
    return x