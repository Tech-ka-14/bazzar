import scipy.stats as stats

def calculate_bayesian_posterior(mu_likelihood: float, sigma_likelihood: float, 
                                 mu_prior: float, sigma_prior: float) -> tuple:
    """
    Combines objective data (likelihood) with personal views (prior) 
    to output Bayesian posterior expected return and volatility.
    """
    var_likelihood = sigma_likelihood**2
    var_prior = sigma_prior**2
    
    # Calculate Posterior Variance (Notice it will be lower than both components)
    posterior_var = 1.0 / ((1.0 / var_likelihood) + (1.0 / var_prior))
    posterior_sigma = posterior_var**0.5
    
    # Calculate Posterior Mean (A weighted average based on certainty)
    posterior_mu = (posterior_var / var_likelihood) * mu_likelihood + \
                   (posterior_var / var_prior) * mu_prior
                   
    return posterior_mu, posterior_sigma

def calculate_bayesian_var(posterior_mu: float, posterior_sigma: float, alpha: float) -> float:
    """Calculates the VaR using the new Bayesian posterior normal parameters."""
    z_score = stats.norm.ppf(1 - alpha)
    return (z_score * posterior_sigma) - posterior_mu