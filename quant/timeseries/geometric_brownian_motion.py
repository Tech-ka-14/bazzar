"""Geometric Brownian motion.

S_t = S_0 exp((mu - sigma^2/2) t + sigma W_t); log returns are normal,
making GBM the canonical continuous-time model for asset prices.
"""

import numpy as np


def simulate_gbm(S0, mu, sigma, T, dt, n_simulations):
    """
    Simulates Geometric Brownian Motion for n_simulations paths.
    Returns the final prices at time T.
    """
    # Number of steps
    n_steps = int(T / dt)

    # Generate all random shocks at once (vectorized for speed)
    Z = np.random.standard_normal((n_simulations, n_steps))

    # Calculate log returns
    log_returns = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z

    # Sum log returns to get total log return over horizon
    total_log_return = np.sum(log_returns, axis=1)

    # Compute final prices
    final_prices = S0 * np.exp(total_log_return)

    return final_prices


def compute(data, mu=None, sigma=None, T=1.0, dt=0.004, n_simulations=1000, seed=None) -> dict:
    """Standard facade: GBM terminal-price simulation summary.

    Parameters:
    data (float): initial price S0 (positive).
    mu (float): drift of the price process.
    sigma (float): volatility of the price process (positive).
    T (float): horizon in years (positive).
    dt (float): simulation time step (positive, <= T).
    n_simulations (int): number of simulated paths.
    seed (int, optional): RNG seed for reproducibility.

    Returns:
    dict: {"s0", "mu", "sigma", "t", "n_simulations",
    "mean_terminal_price", "std_terminal_price", "min_terminal_price",
    "max_terminal_price"} of the simulated terminal prices.
    """
    if mu is None or sigma is None:
        raise ValueError("mu and sigma are required")
    S0 = float(data)
    mu = float(mu)
    sigma = float(sigma)
    T = float(T)
    dt = float(dt)
    if S0 <= 0.0:
        raise ValueError("S0 must be positive")
    if sigma <= 0.0:
        raise ValueError("sigma must be positive")
    if T <= 0.0 or dt <= 0.0 or dt > T:
        raise ValueError("require 0 < dt <= T")
    if int(n_simulations) < 2:
        raise ValueError("n_simulations must be at least 2")

    if seed is not None:
        state = np.random.get_state()
        np.random.seed(seed)
    try:
        final_prices = simulate_gbm(S0, mu, sigma, T, dt, int(n_simulations))
    finally:
        if seed is not None:
            np.random.set_state(state)

    return {
        "s0": S0,
        "mu": mu,
        "sigma": sigma,
        "t": T,
        "n_simulations": int(n_simulations),
        "mean_terminal_price": float(np.mean(final_prices)),
        "std_terminal_price": float(np.std(final_prices)),
        "min_terminal_price": float(np.min(final_prices)),
        "max_terminal_price": float(np.max(final_prices)),
    }
