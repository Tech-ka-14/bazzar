import numpy as np
import scipy.special as sp
from scipy.optimize import minimize

def student_t_garch_loglik(params, returns):
    """
    Calculates the negative log-likelihood of a GARCH(1,1) model 
    with Student-t distributed errors.
    params = [omega, alpha, beta, nu]
    """
    omega, alpha, beta, nu = params
    T = len(returns)
    
    # Enforce strict boundary constraints
    if omega <= 0 or alpha < 0 or beta < 0 or alpha + beta >= 1 or nu <= 2.01:
        return np.inf 
        
    # Initialize variance array with sample variance
    sigma2 = np.zeros(T)
    sigma2[0] = np.var(returns)
    
    log_likelihood = 0.0
    
    # Pre-compute constant gamma terms for efficiency
    term1 = sp.gammaln((nu + 1) / 2) - sp.gammaln(nu / 2) - 0.5 * np.log(np.pi * (nu - 2))
    
    for t in range(1, T):
        # GARCH(1,1) variance recursion
        sigma2[t] = omega + alpha * (returns[t-1]**2) + beta * sigma2[t-1]
        
        # Student-t log-likelihood computation
        term2 = -0.5 * np.log(sigma2[t])
        term3 = -((nu + 1) / 2) * np.log(1 + (returns[t]**2) / ((nu - 2) * sigma2[t]))
        
        log_likelihood += term1 + term2 + term3
        
    # Return negative log-likelihood for the SciPy minimizer
    return -log_likelihood 

# Example implementation
# initial_guess = [0.00001, 0.1, 0.8, 5.0] # omega, alpha, beta, nu
# bounds = ((1e-6, None), (0.001, 0.99), (0.001, 0.99), (2.01, 100))
# result = minimize(student_t_garch_loglik, initial_guess, args=(returns,), bounds=bounds)