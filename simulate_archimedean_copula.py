import numpy as np
import scipy.stats as stats

def simulate_bivariate_clayton(n_simulations, alpha, marginal_1_dist, marginal_2_dist):
    """
    Simulates correlated asset returns using a Clayton Copula (Algorithm 1).
    The Clayton copula is famous for modelling strong lower-tail dependence (joint crashes).
    
    alpha: Copula parameter governing dependence intensity.
    marginal_1_dist, marginal_2_dist: SciPy frozen continuous distributions (e.g., stats.norm(loc=0, scale=1))
    """
    # Step 1: Generate independent uniform random variables
    u1 = np.random.uniform(0, 1, n_simulations)
    v = np.random.uniform(0, 1, n_simulations)
    
    # Step 2: Apply the Clayton Inverse Conditional Copula to get u2
    # Equation II.6.92
    inner_term = 1 + (u1**-alpha) * (v**(-alpha / (1 + alpha)) - 1)
    u2 = inner_term**(-1 / alpha)
    
    # Step 3: Transform uniforms into the target marginal distributions
    asset_1_returns = marginal_1_dist.ppf(u1)
    asset_2_returns = marginal_2_dist.ppf(u2)
    
    return np.column_stack((asset_1_returns, asset_2_returns))

# Example Usage:
# Simulate 1000 days of returns where Asset 1 is Normal and Asset 2 is Student-t, 
# but they crash together according to a Clayton copula.
# np.random.seed(42)
# m1 = stats.norm(loc=0.0005, scale=0.015)
# m2 = stats.t(df=5, loc=0.001, scale=0.02)
# simulated_returns = simulate_bivariate_clayton(1000, alpha=2.0, marginal_1_dist=m1, marginal_2_dist=m2)