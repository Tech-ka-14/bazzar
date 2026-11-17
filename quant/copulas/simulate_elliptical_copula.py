"""Gaussian (elliptical) copula simulation.

Algorithm 2: independent standard normals are correlated via the Cholesky
decomposition of the correlation matrix, mapped through the normal CDF to
copula uniforms, then through the inverse CDFs of the target marginals.
"""

import numpy as np
import scipy.stats as stats


def simulate_gaussian_copula(n_simulations, correlation_matrix, marginal_dists):
    """
    Simulates correlated asset returns using a Gaussian Copula via Cholesky Decomposition (Algorithm 2).

    correlation_matrix: 2D numpy array representing the desired correlation structure.
    marginal_dists: List of SciPy frozen continuous distributions.
    """
    n_assets = len(marginal_dists)

    # Step 1: Generate independent standard normal random variables
    independent_normals = np.random.normal(0, 1, size=(n_assets, n_simulations))

    # Step 2: Inject correlation using the Cholesky Decomposition
    cholesky_lower = np.linalg.cholesky(correlation_matrix)
    correlated_normals = np.dot(cholesky_lower, independent_normals)

    # Step 3: Transform correlated normals to correlated uniforms using the Normal CDF
    correlated_uniforms = stats.norm.cdf(correlated_normals)

    # Step 4: Map uniforms to the target marginal distributions using the Inverse CDF (PPF)
    simulated_returns = np.zeros((n_simulations, n_assets))
    for i in range(n_assets):
        simulated_returns[:, i] = marginal_dists[i].ppf(correlated_uniforms[i, :])

    return simulated_returns


def _build_marginal(spec: dict):
    """Builds a SciPy frozen distribution from a JSON-friendly spec."""
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


def compute(n_simulations: int, correlation_matrix, marginals=None, seed: int = None) -> dict:
    """Standard facade: Gaussian copula simulation summary as a JSON dict.

    Parameters:
    n_simulations (int): Number of simulated vectors (>= 2).
    correlation_matrix: 2-D array-like (k x k), symmetric positive definite.
    marginals (list, optional): k marginal specs, e.g.
    {"type": "norm", "loc": 0.0, "scale": 0.01} or {"type": "t", "df": 5}.
    Defaults to k standard normals.
    seed (int, optional): Seed for reproducible simulation.

    Returns:
    dict: {"n_simulations", "n_assets", "sample_means", "sample_std_devs",
    "sample_correlation"} with plain floats/nested lists.
    """
    correlation_matrix = np.asarray(correlation_matrix, dtype=float)
    if correlation_matrix.ndim != 2 or correlation_matrix.shape[0] != correlation_matrix.shape[1]:
        raise ValueError("correlation_matrix must be square")
    k = correlation_matrix.shape[0]
    n_simulations = int(n_simulations)
    if n_simulations < 2:
        raise ValueError("n_simulations must be at least 2")
    if marginals is None:
        marginals = [{"type": "norm"}] * k
    if len(marginals) != k:
        raise ValueError("marginals must contain one spec per asset")

    marginal_dists = [_build_marginal(spec) for spec in marginals]

    if seed is not None:
        state = np.random.get_state()
        np.random.seed(int(seed))
    try:
        simulated = simulate_gaussian_copula(n_simulations, correlation_matrix, marginal_dists)
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


# Example Usage:
# cov_matrix = np.array([[1.0, 0.7], [0.7, 1.0]])
# m_dists = [stats.norm(0, 0.01), stats.norm(0, 0.02)]
# returns = simulate_gaussian_copula(10000, cov_matrix, m_dists)
