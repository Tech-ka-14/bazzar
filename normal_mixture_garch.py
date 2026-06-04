import numpy as np
from scipy.stats import norm
from scipy.optimize import minimize

def normal_mixture_garch_loglik(params, returns):
    """
    Evaluates the negative log-likelihood for a 2-State Normal Mixture GARCH(1,1).
    params = [omega1, alpha1, beta1, omega2, alpha2, beta2, p]
    """
    w1, a1, b1, w2, a2, b2, p = params
    T = len(returns)
    
    # Boundary constraints
    if any(param <= 0 for param in [w1, w2]) or \
       any(param < 0 for param in [a1, b1, a2, b2]) or \
       (a1 + b1 >= 1) or (a2 + b2 >= 1) or \
       not (0 < p < 1):
        return np.inf

    var1 = np.zeros(T)
    var2 = np.zeros(T)
    
    # Initialize with divergent states
    var1[0] = np.var(returns) * 0.5 # Low volatility state
    var2[0] = np.var(returns) * 2.0 # High volatility state

    log_lik = 0.0

    for t in range(1, T):
        # State 1 and State 2 variance recursions
        var1[t] = w1 + a1 * (returns[t-1]**2) + b1 * var1[t-1]
        var2[t] = w2 + a2 * (returns[t-1]**2) + b2 * var2[t-1]
        
        # Calculate individual densities
        pdf1 = norm.pdf(returns[t], loc=0, scale=np.sqrt(var1[t]))
        pdf2 = norm.pdf(returns[t], loc=0, scale=np.sqrt(var2[t]))
        
        # Mixture density
        mixture_pdf = p * pdf1 + (1 - p) * pdf2
        
        # Accumulate log-likelihood (avoiding log of zero)
        log_lik += np.log(np.maximum(mixture_pdf, 1e-10))
        
    return -log_lik