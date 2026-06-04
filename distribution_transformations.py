import numpy as np
import scipy.stats as stats

def simulate_normal_distribution(u: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """
    Transforms standard uniform variables into normally distributed variables.
    Equivalent to NORMINV in Excel.
    """
    # Phi inverse (standard normal quantile function)
    standard_normals = stats.norm.ppf(u)
    
    # Scale and shift to match desired mean and standard deviation
    x = standard_normals * sigma + mu
    return x

def simulate_student_t_distribution(u: np.ndarray, nu: int, mu: float, sigma: float) -> np.ndarray:
    """
    Transforms standard uniform variables into a general Student t distribution.
    """
    # Standard t inverse
    standard_t = stats.t.ppf(u, df=nu)
    
    # Adjust for the variance of the standard t distribution: nu / (nu - 2)
    scale_factor = np.sqrt((nu - 2) / nu)
    
    x = (standard_t * scale_factor * sigma) + mu
    return x

# Example usage bridging variance reduction with the inverse transform
u_stratified = generate_stratified_uniforms(n_simulations=10000, n_strata=10)
normal_simulations = simulate_normal_distribution(u_stratified, mu=0.0, sigma=0.15)