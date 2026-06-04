import numpy as np
import scipy.stats as stats
import scipy.special as sp

def bivariate_gaussian_copula_density(u1, u2, rho):
    """
    Calculates the density of a bivariate Gaussian Copula.
    """
    # Transform uniform marginals to standard normal quantiles
    xi_1 = stats.norm.ppf(u1)
    xi_2 = stats.norm.ppf(u2)
    
    # Calculate the exponent term
    numerator = (rho**2 * xi_1**2) - (2 * rho * xi_1 * xi_2) + (rho**2 * xi_2**2)
    denominator = 2 * (1 - rho**2)
    
    # Calculate density
    density = (1 - rho**2)**(-0.5) * np.exp(-numerator / denominator)
    return density

def bivariate_student_t_copula_density(u1, u2, rho, nu):
    """
    Calculates the density of a symmetric bivariate Student-t Copula.
    """
    # Transform uniform marginals to Student-t quantiles
    xi_1 = stats.t.ppf(u1, df=nu)
    xi_2 = stats.t.ppf(u2, df=nu)
    
    # Calculate the constant K
    K = (sp.gamma(nu/2) * sp.gamma((nu+2)/2)) / (sp.gamma((nu+1)/2)**2)
    
    # Calculate the main bracket term
    bracket_term = 1 + (1 / (nu * (1 - rho**2))) * (xi_1**2 - 2 * rho * xi_1 * xi_2 + xi_2**2)
    
    # Calculate the marginal adjustment term
    marginal_adj = ((1 + (xi_1**2)/nu) * (1 + (xi_2**2)/nu))**((nu+1)/2)
    
    density = K * (1 - rho**2)**(-0.5) * (bracket_term)**(-(nu+2)/2) * marginal_adj
    return density

def bivariate_normal_mixture_copula_density(u1, u2, pi, rho1, rho2):
    """
    Calculates the density of a bivariate Normal Mixture Copula.
    pi: Weight assigned to the first copula regime (0 <= pi <= 1)
    """
    density_1 = bivariate_gaussian_copula_density(u1, u2, rho1)
    density_2 = bivariate_gaussian_copula_density(u1, u2, rho2)
    
    mixed_density = (pi * density_1) + ((1 - pi) * density_2)
    return mixed_density