"""Monte Carlo variance-reduction samplers.

Generates antithetic uniform samples (second half is 1 - u of the first
half) and stratified uniform samples (even coverage across strata of the
unit interval).
"""

import numpy as np


def generate_antithetic_uniforms(n_simulations: int) -> np.ndarray:
    """
    Generates a uniform sample where the second half is the antithetic pair of the first half.
    """
    half_n = n_simulations // 2
    u_first_half = np.random.uniform(0, 1, half_n)

    # The antithetic pairs
    u_second_half = 1.0 - u_first_half

    return np.concatenate((u_first_half, u_second_half))


def generate_stratified_uniforms(n_simulations: int, n_strata: int) -> np.ndarray:
    """
    Generates a stratified uniform sample to ensure even coverage across the unit interval.
    """
    samples_per_strata = n_simulations // n_strata
    stratified_samples = []

    for k in range(n_strata):
        # Generate random samples mapped strictly to the bounds of the k-th stratum
        u = np.random.uniform(0, 1, samples_per_strata)
        stratum_u = (u + k) / n_strata
        stratified_samples.append(stratum_u)

    return np.concatenate(stratified_samples)


def compute(data, n_strata=10, method="stratified", seed=None) -> dict:
    """Standard facade: variance-reduced uniform sample summary.

    Parameters:
    data (int): number of uniform samples to generate (>= 2).
    n_strata (int): number of strata for the stratified sampler.
    method (str): "stratified" or "antithetic".
    seed (int, optional): RNG seed for reproducibility.

    Returns:
    dict: {"method", "n", "mean", "variance", "min", "max"} of the
    generated samples.
    """
    n = int(data)
    if n < 2:
        raise ValueError("number of simulations must be at least 2")
    if method not in ("stratified", "antithetic"):
        raise ValueError("method must be 'stratified' or 'antithetic'")

    if seed is not None:
        state = np.random.get_state()
        np.random.seed(seed)
    try:
        if method == "stratified":
            if int(n_strata) < 1:
                raise ValueError("n_strata must be a positive integer")
            samples = generate_stratified_uniforms(n, int(n_strata))
        else:
            samples = generate_antithetic_uniforms(n)
    finally:
        if seed is not None:
            np.random.set_state(state)

    return {
        "method": method,
        "n": int(samples.size),
        "mean": float(np.mean(samples)),
        "variance": float(np.var(samples)),
        "min": float(np.min(samples)),
        "max": float(np.max(samples)),
    }
