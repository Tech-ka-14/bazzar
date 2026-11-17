"""Recursive EWMA estimators.

Computes EWMA mean, variance and volatility using the recursion
m_t = lambda * m_{t-1} + (1 - lambda) * x_t, returning both the full
history and the most recent estimates.
"""

import numpy as np


def calculate_ewma_metrics(data, lambda_param):
    """
    Computes the Exponentially Weighted Moving Average (EWMA) for mean,
    variance, and volatility.

    Parameters:
    data (list or numpy array): The time series of returns/data.
    lambda_param (float): The smoothing constant (0 < lambda < 1).
                          Common choices: 0.94 (daily), 0.97 (monthly).

    Returns:
    dict: A dictionary containing the EWMA series for mean, variance,
          volatility, and the final (most recent) estimates.
    """
    data = np.array(data)
    n = len(data)

    # Pre-allocate arrays for the metrics
    ewma_mean = np.zeros(n)
    ewma_variance = np.zeros(n)
    ewma_volatility = np.zeros(n)

    # Initialization (starting with the first observation)
    # Note: In practice, initialization can vary. Using the first data point is standard.
    ewma_mean[0] = data[0]
    ewma_variance[0] = 0  # Variance starts at 0 for a single point
    ewma_volatility[0] = 0

    # Recursive Calculation
    for t in range(1, n):
        # 1. EWMA Mean
        ewma_mean[t] = lambda_param * ewma_mean[t - 1] + (1 - lambda_param) * data[t]

        # 2. EWMA Variance (Squared deviations from the recursive mean)
        ewma_variance[t] = (
            lambda_param * ewma_variance[t - 1]
            + (1 - lambda_param) * (data[t] - ewma_mean[t - 1]) ** 2
        )

        # 3. EWMA Volatility
        ewma_volatility[t] = np.sqrt(ewma_variance[t])

    # Return the results
    return {
        "mean_series": ewma_mean,
        "variance_series": ewma_variance,
        "volatility_series": ewma_volatility,
        "final_mean": ewma_mean[-1],
        "final_variance": ewma_variance[-1],
        "final_volatility": ewma_volatility[-1],
    }


def compute(data, lambda_param: float = 0.94) -> dict:
    """Standard facade: EWMA estimates as a JSON-serializable dict.

    Parameters:
    data: 1-D array-like of observations.
    lambda_param (float): EWMA smoothing constant in (0, 1); common choices
    are 0.94 (daily) and 0.97 (monthly).

    Returns:
    dict: {"n", "lambda", "final_mean", "final_variance",
    "final_volatility"} with plain floats.
    """
    data = np.asarray(data, dtype=float).ravel()
    if data.size == 0:
        raise ValueError("data must contain at least one observation")
    lambda_param = float(lambda_param)
    if not 0.0 < lambda_param < 1.0:
        raise ValueError("lambda_param must be in the open interval (0, 1)")

    results = calculate_ewma_metrics(data, lambda_param)
    return {
        "n": int(data.size),
        "lambda": lambda_param,
        "final_mean": float(results["final_mean"]),
        "final_variance": float(results["final_variance"]),
        "final_volatility": float(results["final_volatility"]),
    }


if __name__ == "__main__":
    # Example Usage:
    # Let's simulate some returns data with volatility clustering (common in finance)
    np.random.seed(42)

    # Create a synthetic dataset: 100 days of low vol, 100 days of high vol
    low_vol_returns = np.random.normal(0, 0.01, 100)
    high_vol_returns = np.random.normal(0, 0.05, 100)
    synthetic_returns = np.concatenate((low_vol_returns, high_vol_returns))

    # Calculate EWMA with a standard daily lambda of 0.94
    results = calculate_ewma_metrics(synthetic_returns, lambda_param=0.94)

    # Print some results to show it worked
    print(f"Final EWMA Mean: {results['final_mean']:.5f}")
    print(f"Final EWMA Volatility: {results['final_volatility']:.5f}")

    # Let's check the volatility during the low vol period (e.g., at index 99)
    # vs the high vol period (at index 199)
    print(f"Volatility at index 99 (Low Vol Regime): {results['volatility_series'][99]:.5f}")
    print(f"Volatility at index 199 (High Vol Regime): {results['volatility_series'][199]:.5f}")
