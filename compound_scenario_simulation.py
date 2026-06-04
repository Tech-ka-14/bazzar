import numpy as np

def simulate_mixture_scenario_var(probs: list, means: list, stds: list, 
                                  n_simulations: int, alpha: float) -> tuple:
    """
    Simulates a compound return distribution from a mixture of normal scenarios 
    (e.g., Ordinary Market vs. Crash Market) to estimate Scenario VaR and ETL.
    """
    n_components = len(probs)
    simulated_returns = np.zeros(n_simulations)
    
    # 1. Draw uniform numbers to dictate the scenario selection
    u = np.random.uniform(0, 1, n_simulations)
    cum_probs = np.cumsum(probs)
    
    for i in range(n_simulations):
        # Determine which scenario component applies based on probability boundaries
        component_idx = np.searchsorted(cum_probs, u[i])
        
        # 2. Simulate return from the selected distribution regime
        simulated_returns[i] = np.random.normal(loc=means[component_idx], scale=stds[component_idx])
        
    # 3. Estimate empirical VaR from the simulated compound distribution
    # Note: Returns are negative in the tail; VaR is expressed as a positive loss
    var = -np.quantile(simulated_returns, alpha)
    
    # ETL is the expected loss given the loss exceeds VaR
    tail_losses = simulated_returns[simulated_returns < -var]
    etl = -np.mean(tail_losses) if len(tail_losses) > 0 else var
    
    return var, etl