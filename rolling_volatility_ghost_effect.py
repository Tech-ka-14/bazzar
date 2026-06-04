import numpy as np
import pandas as pd

def simulate_ghost_effect(T_window=30, total_days=100, shock_day=10, shock_magnitude=0.15):
    """
    Simulates a time series of returns to demonstrate the 'ghost effect' 
    inherent in T-day equally weighted moving average volatility estimates.
    """
    # 1. Generate baseline zero-mean normal returns
    np.random.seed(42)
    returns = np.random.normal(0, 0.01, total_days)
    
    # 2. Inject a single massive market shock (e.g., 15% drop)
    returns[shock_day] = -shock_magnitude
    
    # 3. Calculate rolling T-day variance and volatility
    df = pd.DataFrame({"Returns": returns})
    df['Squared_Returns'] = df['Returns']**2
    
    # The equally weighted variance is the rolling mean of squared returns
    df['Rolling_Variance'] = df['Squared_Returns'].rolling(window=T_window).mean()
    df['Rolling_Volatility'] = np.sqrt(df['Rolling_Variance'])
    
    # 4. Identify the ghost drop
    # The drop happens exactly T_window days after the shock_day
    ghost_day = shock_day + T_window
    
    return df, shock_day, ghost_day

# Generate the simulation
sim_data, shock_idx, ghost_idx = simulate_ghost_effect(T_window=30)