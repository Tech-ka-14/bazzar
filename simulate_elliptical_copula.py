import numpy as np
import scipy.stats as stats

def simulate_gaussian_copula(n_simulations, correlation_matrix, marginal_dists):
    """
    Simulates correlated asset returns using a Gaussian Copula via Cholesky Decomposition (Algorithm 2).
    
    correlation_matrix: 2D numpy array representing the desired correlation structure.
    marginal_dists: List of SciPy frozen continuous distributions.
    """
    n_assets = len(marginal_dists)
    
    # Step 1: Generate independent standard normal random variables
    independent_normals = np.random.normal(0, 1, size=(n_assets, n_simulations))
    
    # Step 2: Inject correlation using the Cholesky Decomposition
    cholesky_lower = np.linalg.cholesky(correlation_matrix)
    correlated_normals = np.dot(cholesky_lower, independent_normals)
    
    # Step 3: Transform correlated normals to correlated uniforms using the Normal CDF
    correlated_uniforms = stats.norm.cdf(correlated_normals)
    
    # Step 4: Map uniforms to the target marginal distributions using the Inverse CDF (PPF)
    simulated_returns = np.zeros((n_simulations, n_assets))
    for i in range(n_assets):
        simulated_returns[:, i] = marginal_dists[i].ppf(correlated_uniforms[i, :])
        
    return simulated_returns

# Example Usage:
# cov_matrix = np.array([[1.0, 0.7], [0.7, 1.0]])
# m_dists = [stats.norm(0, 0.01), stats.norm(0, 0.02)]
# returns = simulate_gaussian_copula(10000, cov_matrix, m_dists)