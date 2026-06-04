import numpy as np
import scipy.stats as stats

def conditional_gaussian_copula(u2, u1, rho):
    """
    Calculates P(U2 < u2 | U1 = u1) for a bivariate Gaussian copula.
    """
    xi_1 = stats.norm.ppf(u1)
    xi_2 = stats.norm.ppf(u2)
    
    # Equation II.6.61
    z = (xi_2 - rho * xi_1) / np.sqrt(1 - rho**2)
    return stats.norm.cdf(z)

def conditional_student_t_copula(u2, u1, rho, nu):
    """
    Calculates P(U2 < u2 | U1 = u1) for a bivariate Student-t copula.
    """
    xi_1 = stats.t.ppf(u1, df=nu)
    xi_2 = stats.t.ppf(u2, df=nu)
    
    # Equation II.6.68 (adjusted for C_2|1)
    scale_factor = np.sqrt((nu + 1) / (nu + xi_1**2))
    z = scale_factor * ((xi_2 - rho * xi_1) / np.sqrt(1 - rho**2))
    
    # The conditional variable follows a t-distribution with nu + 1 degrees of freedom
    return stats.t.cdf(z, df=nu + 1)

def conditional_clayton_copula(u2, u1, alpha):
    """
    Calculates P(U2 < u2 | U1 = u1) for a bivariate Clayton copula.
    """
    # Equation II.6.73
    term1 = u1**(-(1 + alpha))
    term2 = (u1**-alpha + u2**-alpha - 1)**(-(1 + alpha) / alpha)
    return term1 * term2

def conditional_gumbel_copula(u2, u1, delta):
    """
    Calculates P(U2 < u2 | U1 = u1) for a bivariate Gumbel copula.
    """
    # Prevent log(0)
    u1 = np.clip(u1, 1e-10, 1.0)
    u2 = np.clip(u2, 1e-10, 1.0)
    
    ln_u1 = -np.log(u1)
    ln_u2 = -np.log(u2)
    
    # Equation II.6.76
    bracket_term = ln_u1**delta + ln_u2**delta
    
    term1 = u1**-1
    term2 = ln_u1**(delta - 1)
    term3 = bracket_term**((1 - delta) / delta)
    term4 = np.exp(-(bracket_term**(1 / delta)))
    
    return term1 * term2 * term3 * term4