"""Implicit (elliptical and mixture) copula densities.

Bivariate Gaussian copula density, symmetric Student-t copula density
(Equations II.6.52-II.6.53 region, Alexander 2008), and the normal mixture
copula density as a convex combination of two Gaussian copula densities.
"""

import numpy as np
import scipy.special as sp
import scipy.stats as stats


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
    density = (1 - rho**2) ** (-0.5) * np.exp(-numerator / denominator)
    return density


def bivariate_student_t_copula_density(u1, u2, rho, nu):
    """
    Calculates the density of a symmetric bivariate Student-t Copula.
    """
    # Transform uniform marginals to Student-t quantiles
    xi_1 = stats.t.ppf(u1, df=nu)
    xi_2 = stats.t.ppf(u2, df=nu)

    # Calculate the constant K
    K = (sp.gamma(nu / 2) * sp.gamma((nu + 2) / 2)) / (sp.gamma((nu + 1) / 2) ** 2)

    # Calculate the main bracket term
    bracket_term = 1 + (1 / (nu * (1 - rho**2))) * (xi_1**2 - 2 * rho * xi_1 * xi_2 + xi_2**2)

    # Calculate the marginal adjustment term
    marginal_adj = ((1 + (xi_1**2) / nu) * (1 + (xi_2**2) / nu)) ** ((nu + 1) / 2)

    density = K * (1 - rho**2) ** (-0.5) * (bracket_term) ** (-(nu + 2) / 2) * marginal_adj
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


def compute(
    u1: float,
    u2: float,
    model: str = "gaussian",
    rho: float = 0.0,
    nu: float = 5.0,
    pi: float = 0.5,
    rho1: float = 0.0,
    rho2: float = 0.0,
) -> dict:
    """Standard facade: implicit copula density at a point as a JSON dict.

    Parameters:
    u1 (float): First uniform marginal in (0, 1).
    u2 (float): Second uniform marginal in (0, 1).
    model (str): "gaussian", "student_t" or "normal_mixture".
    rho (float): Correlation parameter for "gaussian"/"student_t", |rho| < 1.
    nu (float): Degrees of freedom for "student_t", positive.
    pi (float): Mixture weight in [0, 1] for "normal_mixture".
    rho1 (float): First correlation for "normal_mixture", |rho1| < 1.
    rho2 (float): Second correlation for "normal_mixture", |rho2| < 1.

    Returns:
    dict: {"model", "u1", "u2", "density"} with plain floats.
    """
    u1 = float(u1)
    u2 = float(u2)
    if not 0.0 < u1 < 1.0 or not 0.0 < u2 < 1.0:
        raise ValueError("u1 and u2 must lie in the open interval (0, 1)")

    if model == "gaussian":
        if not -1.0 < float(rho) < 1.0:
            raise ValueError("rho must satisfy |rho| < 1")
        density = bivariate_gaussian_copula_density(u1, u2, float(rho))
    elif model == "student_t":
        if not -1.0 < float(rho) < 1.0:
            raise ValueError("rho must satisfy |rho| < 1")
        if float(nu) <= 0.0:
            raise ValueError("nu must be positive")
        density = bivariate_student_t_copula_density(u1, u2, float(rho), float(nu))
    elif model == "normal_mixture":
        if not 0.0 <= float(pi) <= 1.0:
            raise ValueError("pi must lie in [0, 1]")
        if not -1.0 < float(rho1) < 1.0 or not -1.0 < float(rho2) < 1.0:
            raise ValueError("rho1 and rho2 must satisfy |rho| < 1")
        density = bivariate_normal_mixture_copula_density(
            u1, u2, float(pi), float(rho1), float(rho2)
        )
    else:
        raise ValueError("model must be 'gaussian', 'student_t' or 'normal_mixture'")

    return {"model": model, "u1": u1, "u2": u2, "density": float(density)}
