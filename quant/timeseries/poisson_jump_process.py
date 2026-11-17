"""Poisson jump process for asset prices.

Jump-diffusion: dS/S = mu dt + sigma dW + (J - 1) dN_t where N_t is a
Poisson process with intensity lambda and jump sizes J are lognormal.
"""

import numpy as np


def simulate_jump_diffusion(S0, mu, sigma, lam, mu_J, sigma_J, T, dt):
    """
    Simulates an asset price following a Poisson jump-diffusion process.

    lam: jump intensity (expected jumps per unit time)
    mu_J: mean of log jump size
    sigma_J: volatility of log jump size
    """
    n_steps = int(T / dt)
    S = np.zeros(n_steps + 1)
    S[0] = S0

    for t in range(1, n_steps + 1):
        # Diffusion component
        Z = np.random.standard_normal()

        # Jump component: number of jumps in dt ~ Poisson(lam * dt)
        N = np.random.poisson(lam * dt)

        jump_impact = 0.0
        if N > 0:
            # Log of jump sizes
            jump_impact = np.sum(np.random.normal(mu_J, sigma_J, N))

        # Log return for this step
        log_return = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z + jump_impact

        S[t] = S[t - 1] * np.exp(log_return)

    return S


def compute(
    data,
    mu=None,
    sigma=None,
    lam=1.0,
    mu_J=0.0,
    sigma_J=0.1,
    T=1.0,
    dt=0.004,
    seed=None,
) -> dict:
    """Standard facade: jump-diffusion path summary as a JSON dict.

    Parameters:
    data (float): initial price S0 (positive).
    mu (float): drift of the diffusion component.
    sigma (float): volatility of the diffusion component (positive).
    lam (float): jump intensity per unit time (non-negative).
    mu_J (float): mean of the log jump size.
    sigma_J (float): volatility of the log jump size (non-negative).
    T (float): horizon in years (positive).
    dt (float): simulation time step (positive, <= T).
    seed (int, optional): RNG seed for reproducibility.

    Returns:
    dict: {"s0", "t", "terminal_price", "total_return", "max_price",
    "min_price", "n_steps"} of the simulated path.
    """
    if mu is None or sigma is None:
        raise ValueError("mu and sigma are required")
    S0 = float(data)
    mu = float(mu)
    sigma = float(sigma)
    lam = float(lam)
    mu_J = float(mu_J)
    sigma_J = float(sigma_J)
    T = float(T)
    dt = float(dt)
    if S0 <= 0.0:
        raise ValueError("S0 must be positive")
    if sigma <= 0.0:
        raise ValueError("sigma must be positive")
    if lam < 0.0:
        raise ValueError("lam must be non-negative")
    if sigma_J < 0.0:
        raise ValueError("sigma_J must be non-negative")
    if T <= 0.0 or dt <= 0.0 or dt > T:
        raise ValueError("require 0 < dt <= T")

    if seed is not None:
        state = np.random.get_state()
        np.random.seed(seed)
    try:
        path = simulate_jump_diffusion(S0, mu, sigma, lam, mu_J, sigma_J, T, dt)
    finally:
        if seed is not None:
            np.random.set_state(state)

    return {
        "s0": S0,
        "t": T,
        "terminal_price": float(path[-1]),
        "total_return": float(path[-1] / path[0] - 1.0),
        "max_price": float(np.max(path)),
        "min_price": float(np.min(path)),
        "n_steps": int(len(path) - 1),
    }
