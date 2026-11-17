"""Copula conditional distributions.

P(U2 < u2 | U1 = u1) for the bivariate Gaussian (Equation II.6.61),
Student-t (II.6.68), Clayton (II.6.73) and Gumbel (II.6.76) copulas
(Alexander 2008); used for simulation and conditional percentile analysis.
"""

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
    term1 = u1 ** (-(1 + alpha))
    term2 = (u1**-alpha + u2**-alpha - 1) ** (-(1 + alpha) / alpha)
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
    term2 = ln_u1 ** (delta - 1)
    term3 = bracket_term ** ((1 - delta) / delta)
    term4 = np.exp(-(bracket_term ** (1 / delta)))

    return term1 * term2 * term3 * term4


def compute(
    u2: float,
    u1: float,
    model: str = "gaussian",
    rho: float = 0.0,
    nu: float = 5.0,
    alpha: float = 1.0,
    delta: float = 2.0,
) -> dict:
    """Standard facade: copula conditional probability as a JSON dict.

    Parameters:
    u2 (float): Conditional quantile evaluated for the second variable,
    in (0, 1).
    u1 (float): Conditioning value of the first variable, in (0, 1).
    model (str): "gaussian", "student_t", "clayton" or "gumbel".
    rho (float): Correlation for "gaussian"/"student_t", |rho| < 1.
    nu (float): Degrees of freedom for "student_t", positive.
    alpha (float): Dependence parameter for "clayton", positive.
    delta (float): Dependence parameter for "gumbel", >= 1.

    Returns:
    dict: {"model", "u1", "u2", "conditional_probability"} with the value
    P(U2 < u2 | U1 = u1) as a plain float.
    """
    u1 = float(u1)
    u2 = float(u2)
    if not 0.0 < u1 < 1.0 or not 0.0 < u2 < 1.0:
        raise ValueError("u1 and u2 must lie in the open interval (0, 1)")

    if model == "gaussian":
        if not -1.0 < float(rho) < 1.0:
            raise ValueError("rho must satisfy |rho| < 1")
        value = conditional_gaussian_copula(u2, u1, float(rho))
    elif model == "student_t":
        if not -1.0 < float(rho) < 1.0:
            raise ValueError("rho must satisfy |rho| < 1")
        if float(nu) <= 0.0:
            raise ValueError("nu must be positive")
        value = conditional_student_t_copula(u2, u1, float(rho), float(nu))
    elif model == "clayton":
        if float(alpha) <= 0.0:
            raise ValueError("alpha must be positive")
        value = conditional_clayton_copula(u2, u1, float(alpha))
    elif model == "gumbel":
        if float(delta) < 1.0:
            raise ValueError("delta must be >= 1")
        value = conditional_gumbel_copula(u2, u1, float(delta))
    else:
        raise ValueError("model must be 'gaussian', 'student_t', 'clayton' or 'gumbel'")

    return {
        "model": model,
        "u1": u1,
        "u2": u2,
        "conditional_probability": float(value),
    }
