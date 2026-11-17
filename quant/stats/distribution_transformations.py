"""Distribution transformations via the inverse CDF.

Transforms standard uniform variables into normal or (variance-standardized)
Student-t draws, equivalent to Excel's NORMINV. Reference: Alexander (2008),
Vol. IV.
"""

import numpy as np
import scipy.stats as stats

from .variance_reduction import generate_stratified_uniforms


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


def compute(data, mu=0.0, sigma=1.0, distribution="normal", nu=5) -> dict:
    """Standard facade: transform uniform samples and summarize the result.

    Parameters:
    data: 1-D array-like of uniform samples in (0, 1), e.g. from
    ``variance_reduction.generate_stratified_uniforms``.
    mu, sigma (float): target mean and standard deviation.
    distribution (str): "normal" or "student_t".
    nu (int): degrees of freedom for the Student-t transform (> 2).

    Returns:
    dict: {"distribution", "n", "mean", "std", "min", "max"} of the
    transformed samples.
    """
    u = np.asarray(data, dtype=float).ravel()
    if u.size == 0 or np.any((u <= 0.0) | (u >= 1.0)):
        raise ValueError("uniform samples must lie in the open interval (0, 1)")

    if distribution == "normal":
        sims = simulate_normal_distribution(u, float(mu), float(sigma))
    elif distribution == "student_t":
        if int(nu) <= 2:
            raise ValueError("nu must exceed 2 for a finite-variance Student-t")
        sims = simulate_student_t_distribution(u, int(nu), float(mu), float(sigma))
    else:
        raise ValueError("distribution must be 'normal' or 'student_t'")

    return {
        "distribution": distribution,
        "n": int(u.size),
        "mean": float(np.mean(sims)),
        "std": float(np.std(sims, ddof=1)),
        "min": float(np.min(sims)),
        "max": float(np.max(sims)),
    }


if __name__ == "__main__":
    # Example usage bridging variance reduction with the inverse transform
    u_stratified = generate_stratified_uniforms(n_simulations=10000, n_strata=10)
    normal_simulations = simulate_normal_distribution(u_stratified, mu=0.0, sigma=0.15)
