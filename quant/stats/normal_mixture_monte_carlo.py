"""Monte Carlo simulation of a two-regime normal mixture.

Each draw is assigned to a crash regime with probability p and simulated
from the corresponding multivariate normal via its Cholesky factor.
Reference: Alexander (2008), Vol. IV.
"""

import numpy as np


def simulate_normal_mixture(
    prob_crash: float,
    mu_crash: np.ndarray,
    cov_crash: np.ndarray,
    mu_normal: np.ndarray,
    cov_normal: np.ndarray,
    n_simulations: int,
) -> np.ndarray:
    """
    Simulates risk factor returns based on a two-regime Normal Mixture distribution.
    """
    k = len(mu_crash)
    simulations = np.zeros((n_simulations, k))

    # Randomly assign each simulation to a regime based on the crash probability
    regime_draws = np.random.binomial(1, prob_crash, n_simulations)

    # Cholesky matrices for both regimes
    chol_crash = np.linalg.cholesky(cov_crash)
    chol_normal = np.linalg.cholesky(cov_normal)

    z = np.random.standard_normal((n_simulations, k))

    for i in range(n_simulations):
        if regime_draws[i] == 1:
            # Crash regime
            simulations[i] = chol_crash @ z[i] + mu_crash
        else:
            # Ordinary regime
            simulations[i] = chol_normal @ z[i] + mu_normal

    return simulations


def compute(
    data,
    prob_crash=None,
    cov_crash=None,
    mu_normal=None,
    cov_normal=None,
    n_simulations=1000,
    seed=None,
) -> dict:
    """Standard facade: two-regime normal-mixture simulation summary.

    Parameters:
    data: crash-regime mean vector (array-like of length k).
    prob_crash (float): probability of the crash regime in [0, 1].
    cov_crash, cov_normal: k x k regime covariance matrices.
    mu_normal: normal-regime mean vector.
    n_simulations (int): number of draws.
    seed (int, optional): RNG seed for reproducibility.

    Returns:
    dict: {"n", "k", "prob_crash", "means", "stds", "covariance"} of the
    simulated risk-factor returns.
    """
    if prob_crash is None or cov_crash is None or mu_normal is None or cov_normal is None:
        raise ValueError("prob_crash, cov_crash, mu_normal and cov_normal are required")
    if not 0.0 <= float(prob_crash) <= 1.0:
        raise ValueError("prob_crash must lie in [0, 1]")
    if int(n_simulations) < 2:
        raise ValueError("n_simulations must be at least 2")

    if seed is not None:
        state = np.random.get_state()
        np.random.seed(seed)
        try:
            sims = simulate_normal_mixture(
                float(prob_crash),
                np.asarray(data, dtype=float),
                np.asarray(cov_crash, dtype=float),
                np.asarray(mu_normal, dtype=float),
                np.asarray(cov_normal, dtype=float),
                int(n_simulations),
            )
        finally:
            np.random.set_state(state)
    else:
        sims = simulate_normal_mixture(
            float(prob_crash),
            np.asarray(data, dtype=float),
            np.asarray(cov_crash, dtype=float),
            np.asarray(mu_normal, dtype=float),
            np.asarray(cov_normal, dtype=float),
            int(n_simulations),
        )

    return {
        "n": int(sims.shape[0]),
        "k": int(sims.shape[1]),
        "prob_crash": float(prob_crash),
        "means": np.mean(sims, axis=0).tolist(),
        "stds": np.std(sims, axis=0, ddof=1).tolist(),
        "covariance": np.cov(sims, rowvar=False).tolist(),
    }
