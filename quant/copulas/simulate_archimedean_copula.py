"""Bivariate Clayton (Archimedean) copula simulation.

Algorithm 1: independent uniforms u1, v are transformed via the Clayton
inverse conditional copula (Equation II.6.92, Alexander 2008), producing
uniforms with strong lower-tail dependence (joint crashes); the uniforms are
then mapped through the inverse CDFs of the target marginals.
"""

import numpy as np


def simulate_bivariate_clayton(n_simulations, alpha, marginal_1_dist, marginal_2_dist):
    """
    Simulates correlated asset returns using a Clayton Copula (Algorithm 1).
    The Clayton copula is famous for modelling strong lower-tail dependence (joint crashes).

    alpha: Copula parameter governing dependence intensity.
    marginal_1_dist, marginal_2_dist: SciPy frozen continuous distributions (e.g., stats.norm(loc=0, scale=1))
    """
    # Step 1: Generate independent uniform random variables
    u1 = np.random.uniform(0, 1, n_simulations)
    v = np.random.uniform(0, 1, n_simulations)

    # Step 2: Apply the Clayton Inverse Conditional Copula to get u2
    # Equation II.6.92
    inner_term = 1 + (u1**-alpha) * (v ** (-alpha / (1 + alpha)) - 1)
    u2 = inner_term ** (-1 / alpha)

    # Step 3: Transform uniforms into the target marginal distributions
    asset_1_returns = marginal_1_dist.ppf(u1)
    asset_2_returns = marginal_2_dist.ppf(u2)

    return np.column_stack((asset_1_returns, asset_2_returns))


def _build_marginal(spec: dict):
    """Builds a SciPy frozen distribution from a JSON-friendly spec."""
    import scipy.stats as stats

    dist_type = spec.get("type", "norm")
    loc = float(spec.get("loc", 0.0))
    scale = float(spec.get("scale", 1.0))
    if scale <= 0.0:
        raise ValueError("marginal 'scale' must be positive")
    if dist_type == "norm":
        return stats.norm(loc=loc, scale=scale)
    if dist_type == "t":
        df = float(spec.get("df", 5.0))
        if df <= 0.0:
            raise ValueError("marginal 'df' must be positive")
        return stats.t(df=df, loc=loc, scale=scale)
    raise ValueError("marginal 'type' must be 'norm' or 't'")


def compute(
    n_simulations: int,
    alpha: float,
    marginal_1: dict = None,
    marginal_2: dict = None,
    seed: int = None,
) -> dict:
    """Standard facade: Clayton copula simulation summary as a JSON dict.

    Parameters:
    n_simulations (int): Number of simulated pairs (>= 2).
    alpha (float): Clayton dependence parameter, positive.
    marginal_1 (dict, optional): Spec for asset 1's marginal, e.g.
    {"type": "norm", "loc": 0.0, "scale": 0.01} or {"type": "t", "df": 5}.
    Defaults to standard normal.
    marginal_2 (dict, optional): Same for asset 2.
    seed (int, optional): Seed for reproducible simulation.

    Returns:
    dict: {"n_simulations", "alpha", "mean_asset_1", "mean_asset_2",
    "std_asset_1", "std_asset_2", "sample_correlation",
    "lower_tail_joint_frequency"} where the last entry is the frequency of
    both assets jointly falling in their bottom 5% of simulated outcomes.
    """
    n_simulations = int(n_simulations)
    alpha = float(alpha)
    if n_simulations < 2:
        raise ValueError("n_simulations must be at least 2")
    if alpha <= 0.0:
        raise ValueError("alpha must be positive for the Clayton copula")

    m1 = _build_marginal(marginal_1 or {"type": "norm"})
    m2 = _build_marginal(marginal_2 or {"type": "norm"})

    if seed is not None:
        state = np.random.get_state()
        np.random.seed(int(seed))
    try:
        simulated = simulate_bivariate_clayton(n_simulations, alpha, m1, m2)
    finally:
        if seed is not None:
            np.random.set_state(state)

    q1, q2 = np.quantile(simulated[:, 0], 0.05), np.quantile(simulated[:, 1], 0.05)
    joint_lower = float(np.mean((simulated[:, 0] <= q1) & (simulated[:, 1] <= q2)))
    return {
        "n_simulations": n_simulations,
        "alpha": alpha,
        "mean_asset_1": float(np.mean(simulated[:, 0])),
        "mean_asset_2": float(np.mean(simulated[:, 1])),
        "std_asset_1": float(np.std(simulated[:, 0], ddof=1)),
        "std_asset_2": float(np.std(simulated[:, 1], ddof=1)),
        "sample_correlation": float(np.corrcoef(simulated.T)[0, 1]),
        "lower_tail_joint_frequency": joint_lower,
    }


# Example Usage:
# Simulate 1000 days of returns where Asset 1 is Normal and Asset 2 is Student-t,
# but they crash together according to a Clayton copula.
# np.random.seed(42)
# m1 = stats.norm(loc=0.0005, scale=0.015)
# m2 = stats.t(df=5, loc=0.001, scale=0.02)
# simulated_returns = simulate_bivariate_clayton(1000, alpha=2.0, marginal_1_dist=m1, marginal_2_dist=m2)
