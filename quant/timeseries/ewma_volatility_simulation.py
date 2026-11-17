"""EWMA volatility simulation.

Simulates daily log returns whose conditional variance follows the EWMA
recursion sigma^2_t = lambda * sigma^2_{t-1} + (1 - lambda) * r^2_{t-1}
driven by a matrix of standard normal draws (n_simulations x h_days).
"""

import numpy as np


def simulate_ewma_returns(
    z_matrix: np.ndarray, initial_vol: float, initial_return: float, lambda_param: float
) -> np.ndarray:
    """
    Simulates daily log returns where the conditional variance follows an EWMA process.
    z_matrix shape: (n_simulations, h_days)
    """
    n_simulations, h_days = z_matrix.shape
    simulated_returns = np.zeros((n_simulations, h_days))

    # Initialize variance and previous return
    current_variance = np.full(n_simulations, initial_vol**2)
    previous_return = np.full(n_simulations, initial_return)

    for t in range(h_days):
        # Update variance using the EWMA recursion: lambda * var + (1-lambda) * prev_return^2
        current_variance = (lambda_param * current_variance) + (
            (1 - lambda_param) * (previous_return**2)
        )

        # Simulate today's return
        current_vol = np.sqrt(current_variance)
        current_return = current_vol * z_matrix[:, t]
        simulated_returns[:, t] = current_return

        # Prepare for the next step
        previous_return = current_return

    return simulated_returns


def compute(
    z_matrix, initial_vol: float, initial_return: float, lambda_param: float = 0.94
) -> dict:
    """Standard facade: EWMA simulation summary as a JSON-serializable dict.

    Parameters:
    z_matrix: 2-D array-like (n_simulations x h_days) of standard normal draws.
    initial_vol (float): Starting daily volatility, must be positive.
    initial_return (float): Return driving the first variance update.
    lambda_param (float): EWMA smoothing constant in (0, 1).

    Returns:
    dict: {"n_simulations", "h_days", "lambda", "mean_terminal_return",
    "std_terminal_return", "terminal_cross_sectional_volatility"}.
    """
    z_matrix = np.asarray(z_matrix, dtype=float)
    if z_matrix.ndim != 2:
        raise ValueError("z_matrix must be a 2-D array (n_simulations x h_days)")
    if float(initial_vol) <= 0.0:
        raise ValueError("initial_vol must be positive")
    lambda_param = float(lambda_param)
    if not 0.0 < lambda_param < 1.0:
        raise ValueError("lambda_param must be in the open interval (0, 1)")

    simulated = simulate_ewma_returns(
        z_matrix, float(initial_vol), float(initial_return), lambda_param
    )
    terminal_returns = simulated[:, -1]
    return {
        "n_simulations": int(simulated.shape[0]),
        "h_days": int(simulated.shape[1]),
        "lambda": lambda_param,
        "mean_terminal_return": float(np.mean(terminal_returns)),
        "std_terminal_return": float(np.std(terminal_returns)),
        "terminal_cross_sectional_volatility": float(np.std(simulated, axis=0)[-1]),
    }
