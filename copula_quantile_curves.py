import numpy as np
import scipy.stats as stats
from scipy.optimize import brentq

def gaussian_quantile_curve(q, u1, rho):
    """
    Explicit q-quantile curve for the Gaussian Copula.
    Returns the uniform probability u2 given u1 and confidence level q.
    """
    xi_1 = stats.norm.ppf(u1)
    q_norm = stats.norm.ppf(q)
    
    # Equation II.6.62
    u2 = stats.norm.cdf(rho * xi_1 + np.sqrt(1 - rho**2) * q_norm)
    return u2

def student_t_quantile_curve(q, u1, rho, nu):
    """
    Explicit q-quantile curve for the Student-t Copula.
    """
    xi_1 = stats.t.ppf(u1, df=nu)
    q_t = stats.t.ppf(q, df=nu + 1)
    
    # Equation II.6.69
    vol_adjustment = np.sqrt((1 - rho**2) * (1 / (nu + 1)) * (nu + xi_1**2))
    u2 = stats.t.cdf(rho * xi_1 + vol_adjustment * q_t, df=nu)
    return u2

def clayton_quantile_curve(q, u1, alpha):
    """
    Explicit q-quantile curve for the Clayton Copula.
    """
    # Equation II.6.74
    inner_term = 1 + (u1**-alpha) * (q**(-alpha / (1 + alpha)) - 1)
    u2 = inner_term**(-1 / alpha)
    return u2

# --- Numerical Solvers for Complex Copulas ---

def normal_mixture_conditional(u2, u1, pi, rho1, rho2):
    """Helper for numerical inversion of Normal Mixture"""
    # Equation II.6.72
    xi_1 = stats.norm.ppf(u1)
    xi_2 = stats.norm.ppf(u2)
    
    z1 = (xi_2 - rho1 * xi_1) / np.sqrt(1 - rho1**2)
    z2 = (xi_2 - rho2 * xi_1) / np.sqrt(1 - rho2**2)
    
    return pi * stats.norm.cdf(z1) + (1 - pi) * stats.norm.cdf(z2)

def gumbel_quantile_curve_numerical(q, u1, delta):
    """
    Numerically solves for u2 in the Gumbel copula conditional distribution.
    """
    # We import the conditional function from the previous script logically
    from copula_conditional_distributions import conditional_gumbel_copula
    
    # Define the objective function to find the root: C_2|1(u2 | u1) - q = 0
    def objective(u2_guess):
        return conditional_gumbel_copula(u2_guess, u1, delta) - q
    
    # Use Brent's method to find the root between 1e-10 and 1.0 (valid probability space)
    try:
        u2_solution = brentq(objective, 1e-10, 1.0 - 1e-10)
        return u2_solution
    except ValueError:
        return np.nan # Failsafe if the root is not found within the bounds