"""Normal copula with Student-t marginals Monte Carlo simulation.

Draws correlated standard normals via the Cholesky decomposition of the
correlation matrix, maps them through the normal CDF to copula uniforms,
then through the inverse Student-t CDF with per-asset degrees of freedom,
scaled to the requested means and standard deviations.
"""

import numpy as np
import scipy.stats as stats


def simulate_normal_copula_t_marginals(
    correlation_matrix: np.ndarray, dfs: list, means: list, std_devs: list, n_simulations: int
) -> np.ndarray:
    """
    Simulates returns using a Normal Copula but specific Student t marginal distributions.
    """
    k = len(dfs)
    chol_corr = np.linalg.cholesky(correlation_matrix)

    # Steps 1-3: Correlated standard normal variables
    z = np.random.standard_normal((k, n_simulations))
    correlated_normals = chol_corr @ z

    # Step 4: Transform to Normal Copula uniforms
    copula_uniforms = stats.norm.cdf(correlated_normals)

    # Steps 5-6: Map to specific Student t marginals
    simulated_returns = np.zeros((n_simulations, k))
    for i in range(k):
        # Apply inverse Student t with specific degrees of freedom
        t_marginal = stats.t.ppf(copula_uniforms[i], df=dfs[i])

        # Scale to match standard deviation and mean
        scale_factor = np.sqrt((dfs[i] - 2) / dfs[i]) * std_devs[i]
        simulated_returns[:, i] = (t_marginal * scale_factor) + means[i]

    return simulated_returns


def compute(
    correlation_matrix, dfs, means, std_devs, n_simulations: int = 10000, seed: int = None
) -> dict:
    """Standard facade: normal-copula t-marginals simulation summary.

    Parameters:
    correlation_matrix: 2-D array-like (k x k), symmetric positive definite.
    dfs: List of k Student-t degrees of freedom, each > 2.
    means: List of k target means.
    std_devs: List of k target standard deviations, each positive.
    n_simulations (int): Number of Monte Carlo draws (>= 2).
    seed (int, optional): Seed for reproducible simulation.

    Returns:
    dict: {"n_simulations", "n_assets", "sample_means", "sample_std_devs",
    "sample_correlation"} with plain floats/nested lists.
    """
    correlation_matrix = np.asarray(correlation_matrix, dtype=float)
    k = len(dfs)
    if correlation_matrix.shape != (k, k):
        raise ValueError("correlation_matrix must be k x k matching dfs")
    if not (len(means) == len(std_devs) == k):
        raise ValueError("dfs, means and std_devs must have equal length")
    if any(float(df) <= 2.0 for df in dfs):
        raise ValueError("each degrees of freedom must exceed 2 (finite variance)")
    if any(float(s) <= 0.0 for s in std_devs):
        raise ValueError("std_devs must be positive")
    n_simulations = int(n_simulations)
    if n_simulations < 2:
        raise ValueError("n_simulations must be at least 2")

    if seed is not None:
        state = np.random.get_state()
        np.random.seed(int(seed))
    try:
        simulated = simulate_normal_copula_t_marginals(
            correlation_matrix,
            [float(df) for df in dfs],
            [float(m) for m in means],
            [float(s) for s in std_devs],
            n_simulations,
        )
    finally:
        if seed is not None:
            np.random.set_state(state)

    return {
        "n_simulations": n_simulations,
        "n_assets": k,
        "sample_means": [float(m) for m in np.mean(simulated, axis=0)],
        "sample_std_devs": [float(s) for s in np.std(simulated, axis=0, ddof=1)],
        "sample_correlation": np.corrcoef(simulated, rowvar=False).tolist(),
    }
