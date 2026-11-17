"""Student-t VaR with approximate horizon scaling.

VaR = t_inv(1-alpha; nu) * sigma * sqrt(((nu - 2)/nu) * h); valid for
small horizons h before the CLT normalizes the aggregated returns.
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.2.8.
"""

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


def compute(sigma: float, h: int = 1, alpha: float = 0.01, nu: float = 5.0) -> dict:
    """Standard facade: Student-t VaR as a JSON-serializable dict.

    Parameters:
    sigma (float): 1-day volatility (positive).
    h (int): Risk horizon in days (>= 1).
    alpha (float): Tail probability in (0, 1), e.g. 0.01.
    nu (float): Degrees of freedom, must be > 2.

    Returns:
    dict: {"method", "alpha", "h", "nu", "var"} with "var" the positive
    loss fraction.
    """
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    if int(h) < 1:
        raise ValueError("h must be a positive integer")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")
    if nu <= 2:
        raise ValueError("nu must be greater than 2 for a defined variance")

    var = calculate_student_t_var(float(sigma), int(h), float(alpha), float(nu))
    return {
        "method": "student_t",
        "alpha": float(alpha),
        "h": int(h),
        "nu": float(nu),
        "var": float(var),
    }
