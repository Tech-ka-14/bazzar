import numpy as np

def simulate_normal_mixture(prob_crash: float, 
                            mu_crash: np.ndarray, cov_crash: np.ndarray,
                            mu_normal: np.ndarray, cov_normal: np.ndarray,
                            n_simulations: int) -> np.ndarray:
    """
    Simulates risk factor returns based on a two-regime Normal Mixture distribution.
    """
    k = len(mu_crash)
    simulations = np.zeros((n_simulations, k))
    
    # Randomly assign each simulation to a regime based on the crash probability
    regime_draws = np.random.binomial(1, prob_crash, n_simulations)
    
    # Cholesky matrices for both regimes
    chol_crash = np.linalg.cholesky(cov_crash)
    chol_normal = np.linalg.cholesky(cov_normal)
    
    z = np.random.standard_normal((n_simulations, k))
    
    for i in range(n_simulations):
        if regime_draws[i] == 1:
            # Crash regime
            simulations[i] = chol_crash @ z[i] + mu_crash
        else:
            # Ordinary regime
            simulations[i] = chol_normal @ z[i] + mu_normal
            
    return simulations