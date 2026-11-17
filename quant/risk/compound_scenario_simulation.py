"""Compound scenario simulation for mixture VaR and ETL.

Simulates returns from a mixture of normal scenarios (e.g. ordinary vs
crash market regimes) and estimates the empirical VaR and Expected Tail
Loss of the compound distribution.
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.2.7.
"""

import numpy as np


def simulate_mixture_scenario_var(
    probs: list, means: list, stds: list, n_simulations: int, alpha: float
) -> tuple:
    """
    Simulates a compound return distribution from a mixture of normal scenarios
    (e.g., Ordinary Market vs. Crash Market) to estimate Scenario VaR and ETL.
    """
    n_components = len(probs)
    if not (len(means) == len(stds) == n_components):
        raise ValueError("probs, means and stds must have equal length")
    simulated_returns = np.zeros(n_simulations)

    # 1. Draw uniform numbers to dictate the scenario selection
    u = np.random.uniform(0, 1, n_simulations)
    cum_probs = np.cumsum(probs)

    for i in range(n_simulations):
        # Determine which scenario component applies based on probability boundaries
        component_idx = np.searchsorted(cum_probs, u[i])

        # 2. Simulate return from the selected distribution regime
        simulated_returns[i] = np.random.normal(loc=means[component_idx], scale=stds[component_idx])

    # 3. Estimate empirical VaR from the simulated compound distribution
    # Note: Returns are negative in the tail; VaR is expressed as a positive loss
    var = -np.quantile(simulated_returns, alpha)

    # ETL is the expected loss given the loss exceeds VaR
    tail_losses = simulated_returns[simulated_returns < -var]
    etl = -np.mean(tail_losses) if len(tail_losses) > 0 else var

    return var, etl


def compute(
    probs, means, stds, n_simulations: int = 10000, alpha: float = 0.01, seed: int = None
) -> dict:
    """Standard facade: compound scenario VaR/ETL as a JSON-serializable dict.

    Parameters:
    probs: Scenario probabilities (positive, summing to 1).
    means: Scenario mean returns.
    stds: Scenario volatilities (positive).
    n_simulations (int): Number of Monte Carlo draws.
    alpha (float): Tail probability in (0, 1).
    seed (int, optional): RNG seed for reproducibility.

    Returns:
    dict: {"method", "alpha", "n_simulations", "var", "etl"} with
    positive loss fractions.
    """
    probs = [float(p) for p in probs]
    if not probs or any(p <= 0 for p in probs) or abs(sum(probs) - 1.0) > 1e-9:
        raise ValueError("probs must be positive and sum to 1")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")
    if seed is not None:
        np.random.seed(seed)

    var, etl = simulate_mixture_scenario_var(
        probs, list(means), list(stds), int(n_simulations), float(alpha)
    )
    return {
        "method": "compound_scenario",
        "alpha": float(alpha),
        "n_simulations": int(n_simulations),
        "var": float(var),
        "etl": float(etl),
    }
