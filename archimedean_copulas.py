import numpy as np

def bivariate_clayton_copula_density(u1, u2, alpha):
    """
    Calculates the density of a bivariate Clayton Copula.
    Captures lower tail dependence (assets crashing together).
    alpha: Copula parameter (alpha > 0)
    """
    if alpha <= 0:
        raise ValueError("Alpha parameter for Clayton copula must be > 0")
        
    term1 = alpha + 1
    term2 = (u1**-alpha + u2**-alpha - 1)**(-2 - (1/alpha))
    term3 = (u1**(-alpha - 1)) * (u2**(-alpha - 1))
    
    density = term1 * term2 * term3
    lower_tail_dependence = 2**(-1/alpha)
    
    return {"density": density, "lambda_lower": lower_tail_dependence, "lambda_upper": 0.0}

def bivariate_gumbel_copula_density(u1, u2, delta):
    """
    Calculates the density of a bivariate Gumbel Copula.
    Captures upper tail dependence (assets spiking together).
    delta: Copula parameter (delta >= 1)
    """
    if delta < 1:
        raise ValueError("Delta parameter for Gumbel copula must be >= 1")
        
    # Prevent log(0) errors
    u1 = np.clip(u1, 1e-10, 1.0)
    u2 = np.clip(u2, 1e-10, 1.0)
    
    ln_u1 = -np.log(u1)
    ln_u2 = -np.log(u2)
    
    # Calculate 'A' term
    A = (ln_u1**delta + ln_u2**delta)**(1/delta)
    
    term1 = A + delta - 1
    term2 = A**(1 - 2*delta)
    term3 = np.exp(-A)
    term4 = 1 / (u1 * u2)
    term5 = (ln_u1**(delta - 1)) * (ln_u2**(delta - 1))
    
    density = term1 * term2 * term3 * term4 * term5
    upper_tail_dependence = 2 - 2**(1/delta)
    
    return {"density": density, "lambda_lower": 0.0, "lambda_upper": upper_tail_dependence}