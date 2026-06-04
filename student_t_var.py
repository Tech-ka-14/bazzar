import numpy as np
import scipy.stats as stats

def calculate_student_t_var(sigma: float, h: int, alpha: float, nu: float) -> float:
    """
    Calculates the Student t VaR, scaling approximately for horizon h.
    Valid mostly for small h, before the Central Limit Theorem normalizes the sum.
    """
    # Inverse cumulative distribution function for Student t
    t_inv = stats.t.ppf(1 - alpha, df=nu)
    
    # Variance adjustment factor
    variance_adj = np.sqrt(((nu - 2) / nu) * h)
    
    return variance_adj * t_inv * sigma