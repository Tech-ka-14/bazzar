"""Empirical Expected Tail Loss (ETL) from a historical return series.

The empirical ETL is the average of the historical losses strictly worse
than a given VaR threshold (positive loss percentage).
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.1.4.
"""

import numpy as np


def calculate_empirical_etl(historical_returns: np.ndarray, var_percentage: float) -> float:
    """
    Calculates the Empirical Expected Tail Loss (ETL) from a historical returns distribution.

    Parameters:
    historical_returns (np.ndarray): Array of historically simulated portfolio returns.
    var_percentage (float): The previously calculated VaR (expressed as a positive loss percentage).

    Returns:
    float: The Empirical ETL (expressed as a positive loss percentage).
    """
    # Isolate the returns that represent losses strictly worse than the VaR threshold
    tail_losses = historical_returns[historical_returns < -var_percentage]

    if len(tail_losses) == 0:
        return var_percentage  # Fallback if no returns breach the threshold

    # ETL is the expected (average) severity of these extreme losses
    empirical_etl = -np.mean(tail_losses)

    return empirical_etl


# Conceptual Demonstration


def compute(returns, var_percentage: float) -> dict:
    """Standard facade: empirical ETL given a VaR threshold as a JSON dict.

    Parameters:
    returns: 1-D array-like of historical returns (fractions).
    var_percentage (float): VaR expressed as a positive loss fraction
    (non-negative).

    Returns:
    dict: {"method", "n", "var", "etl"}.
    """
    returns = np.asarray(returns, dtype=float).ravel()
    if returns.size == 0:
        raise ValueError("returns must contain at least one observation")
    if var_percentage < 0:
        raise ValueError("var_percentage must be a non-negative loss fraction")

    etl = calculate_empirical_etl(returns, float(var_percentage))
    return {
        "method": "empirical_etl",
        "n": int(returns.size),
        "var": float(var_percentage),
        "etl": float(etl),
    }


if __name__ == "__main__":
    np.random.seed(42)
    mock_returns = np.random.normal(0.001, 0.02, 5000)

    # Assuming we already found the 1% VaR
    var_1_pct = 0.0455  # 4.55% VaR

    emp_etl = calculate_empirical_etl(mock_returns, var_1_pct)
    print(f"Empirical 1% VaR: {var_1_pct:.2%}")
    print(f"Empirical 1% Expected Tail Loss (ETL): {emp_etl:.2%}")
