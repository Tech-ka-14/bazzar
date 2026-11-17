"""Inverse transform sampling.

Applies the inverse CDF (percent point function) to standard uniform samples
to simulate normal, Student-t or lognormal marginals.
"""

import numpy as np
import scipy.stats as stats


def simulate_marginals_from_uniform(u_samples, distribution_type="normal", **kwargs):
    """
    Simulates random variables from a specified marginal distribution
    by applying the inverse CDF (Percent Point Function) to standard uniform samples.
    """
    # Ensure u_samples are valid uniform probabilities (0 < u < 1)
    u_samples = np.clip(u_samples, 1e-10, 1 - 1e-10)

    if distribution_type == "normal":
        # Default to standard normal if no args provided
        loc = kwargs.get("loc", 0.0)
        scale = kwargs.get("scale", 1.0)
        return stats.norm.ppf(u_samples, loc=loc, scale=scale)

    elif distribution_type == "student_t":
        df = kwargs.get("df", 5)  # degrees of freedom
        return stats.t.ppf(u_samples, df=df)

    elif distribution_type == "lognormal":
        s = kwargs.get("s", 1.0)  # shape parameter
        return stats.lognorm.ppf(u_samples, s=s)

    else:
        raise ValueError(f"Distribution {distribution_type} not supported.")


def compute(data, distribution_type="normal", seed=None, **kwargs) -> dict:
    """Standard facade: simulate from a marginal via inverse transform.

    Parameters:
    data (int): number of uniform draws to generate and transform.
    distribution_type (str): "normal", "student_t" or "lognormal".
    seed (int, optional): RNG seed for reproducibility.
    **kwargs: forwarded to ``simulate_marginals_from_uniform`` (e.g.
    ``loc``, ``scale``, ``df``, ``s``).

    Returns:
    dict: {"distribution", "n", "mean", "std", "min", "max"} of the
    simulated samples.
    """
    n = int(data)
    if n < 2:
        raise ValueError("number of simulations must be at least 2")

    rng = np.random.default_rng(seed)
    uniforms = rng.uniform(0.0, 1.0, n)
    sims = simulate_marginals_from_uniform(uniforms, distribution_type=distribution_type, **kwargs)
    return {
        "distribution": distribution_type,
        "n": n,
        "mean": float(np.mean(sims)),
        "std": float(np.std(sims, ddof=1)),
        "min": float(np.min(sims)),
        "max": float(np.max(sims)),
    }


if __name__ == "__main__":
    # Example: Generate 1000 uniform variables and transform them into a Student-t distribution
    np.random.seed(42)
    uniform_draws = np.random.uniform(0, 1, 1000)
    simulated_t_returns = simulate_marginals_from_uniform(
        uniform_draws, distribution_type="student_t", df=4
    )
