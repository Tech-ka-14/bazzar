import numpy as np
import scipy.stats as stats

def simulate_marginals_from_uniform(u_samples, distribution_type='normal', **kwargs):
    """
    Simulates random variables from a specified marginal distribution 
    by applying the inverse CDF (Percent Point Function) to standard uniform samples.
    """
    # Ensure u_samples are valid uniform probabilities (0 < u < 1)
    u_samples = np.clip(u_samples, 1e-10, 1 - 1e-10)
    
    if distribution_type == 'normal':
        # Default to standard normal if no args provided
        loc = kwargs.get('loc', 0.0)
        scale = kwargs.get('scale', 1.0)
        return stats.norm.ppf(u_samples, loc=loc, scale=scale)
        
    elif distribution_type == 'student_t':
        df = kwargs.get('df', 5) # degrees of freedom
        return stats.t.ppf(u_samples, df=df)
        
    elif distribution_type == 'lognormal':
        s = kwargs.get('s', 1.0) # shape parameter
        return stats.lognorm.ppf(u_samples, s=s)
        
    else:
        raise ValueError(f"Distribution {distribution_type} not supported.")

# Example: Generate 1000 uniform variables and transform them into a Student-t distribution
np.random.seed(42)
uniform_draws = np.random.uniform(0, 1, 1000)
simulated_t_returns = simulate_marginals_from_uniform(uniform_draws, distribution_type='student_t', df=4)