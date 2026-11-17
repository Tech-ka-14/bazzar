"""A-GARCH volatility simulation.

Simulates daily log returns whose conditional variance follows the asymmetric
GARCH(1,1) recursion sigma^2_t = omega + alpha*(r_{t-1} - lambda)^2 +
beta*sigma^2_{t-1}, driven by a matrix of standard normal draws
(n_simulations x h_days).
"""

import numpy as np


def simulate_agarch_returns(
    z_matrix: np.ndarray,
    initial_vol: float,
    initial_return: float,
    omega: float,
    alpha: float,
    beta: float,
    lambda_asym: float,
) -> np.ndarray:
    """
    Simulates daily log returns incorporating A-GARCH volatility and mean reversion.
    z_matrix shape: (n_simulations, h_days) containing standard normal draws.
    """
    n_simulations, h_days = z_matrix.shape
    simulated_returns = np.zeros((n_simulations, h_days))

    # Initialize variance for the first step
    current_variance = np.full(n_simulations, initial_vol**2)
    previous_return = np.full(n_simulations, initial_return)

    for t in range(h_days):
        # Update variance using the A-GARCH recurrence
        # Note: the text uses lambda for the asymmetry shift here, separate from EWMA's lambda
        shock_term = (previous_return - lambda_asym) ** 2
        current_variance = omega + (alpha * shock_term) + (beta * current_variance)
        current_vol = np.sqrt(current_variance)

        # Simulate today's return
        current_return = current_vol * z_matrix[:, t]
        simulated_returns[:, t] = current_return

        # Prepare for the next step
        previous_return = current_return

    return simulated_returns


def compute(
    z_matrix,
    initial_vol: float,
    initial_return: float,
    omega: float,
    alpha: float,
    beta: float,
    lambda_asym: float = 0.0,
) -> dict:
    """Standard facade: A-GARCH simulation summary as a JSON dict.

    Parameters:
    z_matrix: 2-D array-like (n_simulations x h_days) of standard normal draws.
    initial_vol (float): Starting daily volatility, must be positive.
    initial_return (float): Return driving the first variance update.
    omega (float): Constant variance term, must be positive.
    alpha (float): ARCH coefficient on the shifted squared return (>= 0).
    beta (float): GARCH coefficient on lagged variance (>= 0).
    lambda_asym (float): Asymmetry shift parameter.

    Returns:
    dict: {"n_simulations", "h_days", "mean_terminal_return",
    "std_terminal_return", "terminal_cross_sectional_volatility"}.
    """
    z_matrix = np.asarray(z_matrix, dtype=float)
    if z_matrix.ndim != 2:
        raise ValueError("z_matrix must be a 2-D array (n_simulations x h_days)")
    if float(initial_vol) <= 0.0:
        raise ValueError("initial_vol must be positive")
    if float(omega) <= 0.0:
        raise ValueError("omega must be positive")
    if float(alpha) < 0.0 or float(beta) < 0.0:
        raise ValueError("alpha and beta must be non-negative")

    simulated = simulate_agarch_returns(
        z_matrix,
        float(initial_vol),
        float(initial_return),
        float(omega),
        float(alpha),
        float(beta),
        float(lambda_asym),
    )
    terminal_returns = simulated[:, -1]
    return {
        "n_simulations": int(simulated.shape[0]),
        "h_days": int(simulated.shape[1]),
        "mean_terminal_return": float(np.mean(terminal_returns)),
        "std_terminal_return": float(np.std(terminal_returns)),
        "terminal_cross_sectional_volatility": float(np.std(simulated, axis=0)[-1]),
    }
