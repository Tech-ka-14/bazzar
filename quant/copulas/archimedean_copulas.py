"""Bivariate Archimedean copula densities (Clayton and Gumbel).

Clayton (alpha > 0) captures lower tail dependence, lambda_L = 2^(-1/alpha);
Gumbel (delta >= 1) captures upper tail dependence, lambda_U = 2 - 2^(1/delta).
Kendall's tau has closed forms: Clayton tau = alpha / (alpha + 2), Gumbel
tau = 1 - 1/delta (Nelsen 2006, An Introduction to Copulas, Ch. 4-5).
"""

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
    term2 = (u1**-alpha + u2**-alpha - 1) ** (-2 - (1 / alpha))
    term3 = (u1 ** (-alpha - 1)) * (u2 ** (-alpha - 1))

    density = term1 * term2 * term3
    lower_tail_dependence = 2 ** (-1 / alpha)

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
    A = (ln_u1**delta + ln_u2**delta) ** (1 / delta)

    term1 = A + delta - 1
    term2 = A ** (1 - 2 * delta)
    term3 = np.exp(-A)
    term4 = 1 / (u1 * u2)
    term5 = (ln_u1 ** (delta - 1)) * (ln_u2 ** (delta - 1))

    density = term1 * term2 * term3 * term4 * term5
    upper_tail_dependence = 2 - 2 ** (1 / delta)

    return {"density": density, "lambda_lower": 0.0, "lambda_upper": upper_tail_dependence}


def kendall_tau_clayton(alpha):
    """
    Closed-form Kendall's tau of the bivariate Clayton copula:
    tau = alpha / (alpha + 2). Requires alpha > 0.
    """
    if alpha <= 0:
        raise ValueError("Alpha parameter for Clayton copula must be > 0")
    return alpha / (alpha + 2.0)


def kendall_tau_gumbel(delta):
    """
    Closed-form Kendall's tau of the bivariate Gumbel copula:
    tau = 1 - 1 / delta. Requires delta >= 1.
    """
    if delta < 1:
        raise ValueError("Delta parameter for Gumbel copula must be >= 1")
    return 1.0 - 1.0 / delta


def compute(family: str, theta: float, u1: float = None, u2: float = None) -> dict:
    """Standard facade: Archimedean copula summary as a JSON dict.

    Parameters:
    family (str): "clayton" or "gumbel".
    theta (float): Copula parameter (alpha for Clayton > 0; delta for
    Gumbel >= 1).
    u1, u2 (float, optional): Pseudo-observations in (0, 1]; when both are
    given, the copula density at (u1, u2) is included.

    Returns:
    dict: {"family", "theta", "kendall_tau", "lambda_lower", "lambda_upper",
    "density" (only when u1 and u2 are given)} with plain floats.
    """
    family = str(family).lower()
    theta = float(theta)
    if family == "clayton":
        kendall_tau = float(kendall_tau_clayton(theta))
        summary = {
            "kendall_tau": kendall_tau,
            "lambda_lower": float(2 ** (-1.0 / theta)),
            "lambda_upper": 0.0,
        }
        if u1 is not None and u2 is not None:
            summary["density"] = float(bivariate_clayton_copula_density(u1, u2, theta)["density"])
    elif family == "gumbel":
        kendall_tau = float(kendall_tau_gumbel(theta))
        summary = {
            "kendall_tau": kendall_tau,
            "lambda_lower": 0.0,
            "lambda_upper": float(2.0 - 2 ** (1.0 / theta)),
        }
        if u1 is not None and u2 is not None:
            summary["density"] = float(bivariate_gumbel_copula_density(u1, u2, theta)["density"])
    else:
        raise ValueError("family must be 'clayton' or 'gumbel'")

    return {"family": family, "theta": theta, **summary}
