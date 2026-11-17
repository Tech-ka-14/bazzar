"""Discrete-time stochastic processes.

Random walks with drift, the AR(1) mean-reverting process (stationarity
condition |phi| < 1), and the MA(1) process (invertibility condition
|theta| < 1), with simulation and conditional moments.
"""

import numpy as np


def simulate_random_walk_drift(y0, mu, sigma_epsilon, n_steps):
    """
    Simulates a random walk with drift.

    Y_t = mu + Y_{t-1} + epsilon_t
    """
    y = np.zeros(n_steps)
    y[0] = y0
    epsilon = np.random.normal(0, sigma_epsilon, n_steps)
    for t in range(1, n_steps):
        y[t] = mu + y[t - 1] + epsilon[t]
    return y


def simulate_ar1(y0, alpha, phi, sigma_epsilon, n_steps):
    """
    Simulates a first-order autoregressive (AR1) process.

    Y_t = alpha + phi * Y_{t-1} + epsilon_t
    """
    if abs(phi) >= 1:
        raise ValueError("For a stationary AR(1) process, |phi| must be < 1.")
    y = np.zeros(n_steps)
    y[0] = y0
    epsilon = np.random.normal(0, sigma_epsilon, n_steps)
    for t in range(1, n_steps):
        y[t] = alpha + phi * y[t - 1] + epsilon[t]
    return y


def simulate_ma1(mu, theta, sigma_epsilon, n_steps):
    """
    Simulates a first-order moving average (MA1) process.

    X_t = mu + epsilon_t + theta * epsilon_{t-1}
    """
    if abs(theta) >= 1:
        raise ValueError("For an invertible MA(1) process, |theta| must be < 1.")
    epsilon = np.random.normal(0, sigma_epsilon, n_steps + 1)
    x = np.zeros(n_steps)
    for t in range(n_steps):
        x[t] = mu + epsilon[t + 1] + theta * epsilon[t]
    return x


def ar1_conditional_moments(y_t, alpha, phi, sigma_epsilon, h):
    """
    Calculates the exact conditional expectation and variance of an AR(1)
    process h steps ahead.
    """
    expectation = alpha * sum(phi**i for i in range(h)) + (phi**h) * y_t
    variance = sigma_epsilon**2 * sum(phi ** (2 * i) for i in range(h))
    return expectation, variance


def compute(data, alpha=None, phi=None, sigma_epsilon=None, h=None) -> dict:
    """Standard facade: AR(1) conditional moments as a JSON dict.

    Parameters:
    data (float): current state y_t of the AR(1) process.
    alpha (float): intercept of the AR(1) recursion.
    phi (float): autoregressive coefficient; |phi| < 1 for stationarity.
    sigma_epsilon (float): innovation volatility (positive).
    h (int): forecast horizon in steps (>= 1).

    Returns:
    dict: {"y_t", "alpha", "phi", "h", "expectation", "variance", "std"}.
    """
    if alpha is None or phi is None or sigma_epsilon is None or h is None:
        raise ValueError("alpha, phi, sigma_epsilon and h are required")
    y_t = float(data)
    alpha = float(alpha)
    phi = float(phi)
    sigma_epsilon = float(sigma_epsilon)
    h = int(h)
    if abs(phi) >= 1.0:
        raise ValueError("for a stationary AR(1) process, |phi| must be < 1")
    if sigma_epsilon <= 0.0:
        raise ValueError("sigma_epsilon must be positive")
    if h < 1:
        raise ValueError("h must be at least 1")

    expectation, variance = ar1_conditional_moments(y_t, alpha, phi, sigma_epsilon, h)
    return {
        "y_t": y_t,
        "alpha": alpha,
        "phi": phi,
        "h": h,
        "expectation": float(expectation),
        "variance": float(variance),
        "std": float(np.sqrt(variance)),
    }
