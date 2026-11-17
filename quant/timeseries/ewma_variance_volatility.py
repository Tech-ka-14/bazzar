"""EWMA variance and volatility estimation.

Recursive EWMA variance: sigma^2_t = (1 - lambda) * r_{t-1}^2 + lambda *
sigma^2_{t-1} (Equation IV.2.79, Alexander 2008; RiskMetrics). The recursion
is initialized at the unconditional sample variance unless an explicit
initial variance is supplied.
"""

import numpy as np


def calculate_ewma_variance(
    returns: np.ndarray, lambda_param: float, initial_variance: float = None
) -> np.ndarray:
    """
    Calculates the time series of EWMA variance using the recursive formula (Equation IV.2.79).
    """
    n = len(returns)
    ewma_var = np.zeros(n)

    # Initialize the first variance (often set to the unconditional sample variance or the first squared return)
    ewma_var[0] = initial_variance if initial_variance is not None else np.var(returns)

    # Apply the recursive formula: sigma^2_t = (1 - lambda)*r_{t-1}^2 + lambda*sigma^2_{t-1}
    for t in range(1, n):
        ewma_var[t] = (1 - lambda_param) * (returns[t - 1] ** 2) + (lambda_param * ewma_var[t - 1])

    return ewma_var


def compute(returns, lambda_param: float = 0.94, annualization: int = 1) -> dict:
    """Standard facade: current EWMA volatility as a JSON-serializable dict.

    Parameters:
    returns: 1-D array-like of historical returns (fractions).
    lambda_param (float): EWMA smoothing constant in (0, 1), e.g. 0.94.
    annualization (int): Periods per year used to annualize the current
    volatility (1 = no annualization).

    Returns:
    dict: {"model", "lambda", "n", "current_variance",
    "current_volatility", "annualized_volatility"}.
    """
    returns = np.asarray(returns, dtype=float).ravel()
    if returns.size < 2:
        raise ValueError("returns must contain at least two observations")
    if not 0.0 < lambda_param < 1.0:
        raise ValueError("lambda_param must be in the open interval (0, 1)")

    variances = calculate_ewma_variance(returns, float(lambda_param))
    current_variance = float(variances[-1])
    current_volatility = float(np.sqrt(current_variance))
    return {
        "model": "ewma",
        "lambda": float(lambda_param),
        "n": int(returns.size),
        "current_variance": current_variance,
        "current_volatility": current_volatility,
        "annualized_volatility": float(current_volatility * np.sqrt(int(annualization))),
    }


if __name__ == "__main__":
    # Simulation mimicking the FTSE 100 volatility environment (Figure IV.2.12)
    np.random.seed(42)
    # Creating a series with a sudden volatility spike in the middle
    returns_stable = np.random.normal(0, 0.01, 100)
    returns_crash = np.random.normal(0, 0.04, 20)
    returns_recovery = np.random.normal(0, 0.015, 130)
    mock_returns = np.concatenate([returns_stable, returns_crash, returns_recovery])

    # Calculate EWMA Volatility (Annualized)
    lambda_smooth = 0.94
    days_in_year = 250

    ewma_variances = calculate_ewma_variance(mock_returns, lambda_smooth)
    ewma_volatilities = np.sqrt(ewma_variances * days_in_year)

    print(
        f"Current Estimated Annual EWMA Volatility (lambda={lambda_smooth}): {ewma_volatilities[-1]:.2%}"
    )
