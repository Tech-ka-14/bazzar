import numpy as np
import scipy.stats as stats

def simulate_normal_copula_t_marginals(correlation_matrix: np.ndarray, 
                                       dfs: list, means: list, std_devs: list, 
                                       n_simulations: int) -> np.ndarray:
    """
    Simulates returns using a Normal Copula but specific Student t marginal distributions.
    """
    k = len(dfs)
    chol_corr = np.linalg.cholesky(correlation_matrix)
    
    # Steps 1-3: Correlated standard normal variables
    z = np.random.standard_normal((k, n_simulations))
    correlated_normals = chol_corr @ z
    
    # Step 4: Transform to Normal Copula uniforms
    copula_uniforms = stats.norm.cdf(correlated_normals)
    
    # Steps 5-6: Map to specific Student t marginals
    simulated_returns = np.zeros((n_simulations, k))
    for i in range(k):
        # Apply inverse Student t with specific degrees of freedom
        t_marginal = stats.t.ppf(copula_uniforms[i], df=dfs[i])
        
        # Scale to match standard deviation and mean
        scale_factor = np.sqrt((dfs[i] - 2) / dfs[i]) * std_devs[i]
        simulated_returns[:, i] = (t_marginal * scale_factor) + means[i]
        
    return simulated_returns