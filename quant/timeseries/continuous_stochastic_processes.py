"""Continuous-time stochastic processes.

Geometric Brownian motion (GBM) and the Ornstein-Uhlenbeck (mean-reverting)
process with conditional expectation/variance of the OU state.
"""

import numpy as np


def simulate_gbm(S0, mu, sigma, T, n_steps, n_paths=1000):
    """
    Simulates paths of a Geometric Brownian Motion (GBM).

    dS_t = mu * S_t * dt + sigma * S_t * dW_t
    """
    dt = T / n_steps
    S = np.zeros((n_steps + 1, n_paths))
    S[0] = S0

    for t in range(1, n_steps + 1):
        Z = np.random.standard_normal(n_paths)
        # Exact solution of GBM:
        S[t] = S[t - 1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z)
    return S


def ornstein_uhlenbeck(X0, alpha, mu, sigma, t, dt=0.01):
    """
    Simulates an Ornstein-Uhlenbeck (Mean Reverting) process.

    dX_t = alpha * (mu - X_t) * dt + sigma * dW_t
    """
    n_steps = int(t / dt)
    X = np.zeros(n_steps + 1)
    X[0] = X0

    for i in range(1, n_steps + 1):
        dW = np.random.normal(0, np.sqrt(dt))
        X[i] = X[i - 1] + alpha * (mu - X[i - 1]) * dt + sigma * dW
    return X


def ou_conditional_moments(X0, alpha, mu, sigma, t):
    """
    Calculates the exact conditional expectation and variance of an OU process
    at time t.
    """
    expectation = mu + (X0 - mu) * np.exp(-alpha * t)
    variance = (sigma**2 / (2 * alpha)) * (1 - np.exp(-2 * alpha * t))
    return expectation, variance


def compute(data, alpha=None, mu=None, sigma=None, t=None) -> dict:
    """Standard facade: exact OU conditional moments as a JSON dict.

    Parameters:
    data (float): initial state X0 of the Ornstein-Uhlenbeck process.
    alpha (float): mean-reversion speed (positive).
    mu (float): long-run mean.
    sigma (float): diffusion volatility (positive).
    t (float): horizon for the conditional moments (positive).

    Returns:
    dict: {"x0", "alpha", "mu", "sigma", "t", "expectation", "variance",
    "std"} of the OU process state at time t.
    """
    if alpha is None or mu is None or sigma is None or t is None:
        raise ValueError("alpha, mu, sigma and t are required")
    X0 = float(data)
    alpha = float(alpha)
    mu = float(mu)
    sigma = float(sigma)
    t = float(t)
    if alpha <= 0.0:
        raise ValueError("alpha must be positive")
    if sigma <= 0.0:
        raise ValueError("sigma must be positive")
    if t <= 0.0:
        raise ValueError("t must be positive")

    expectation, variance = ou_conditional_moments(X0, alpha, mu, sigma, t)
    return {
        "x0": X0,
        "alpha": alpha,
        "mu": mu,
        "sigma": sigma,
        "t": t,
        "expectation": float(expectation),
        "variance": float(variance),
        "std": float(np.sqrt(variance)),
    }
