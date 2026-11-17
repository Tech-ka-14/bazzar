"""Standard historical VaR from the empirical return distribution.

Historical VaR is the negative of the linear-interpolated empirical
alpha-quantile of the historical return distribution.
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.1.2.
"""

import numpy as np


def calculate_historical_var(historical_returns: np.ndarray, alpha: float = 0.01) -> float:
    """
    Calculates the Standard Historical VaR based purely on the empirical distribution.

    Parameters:
    historical_returns (np.ndarray): Array of historically simulated portfolio returns.
    alpha (float): Significance level (e.g., 0.01 for 1% VaR).

    Returns:
    float: The Historical VaR as a percentage.
    """
    # Use numpy's quantile function with linear interpolation for non-integer indices
    var_percentile = np.quantile(historical_returns, alpha, method="linear")

    # VaR is the negative of the loss quantile
    return -var_percentile


# --- Conceptual Demonstration ---


def compute(returns, alpha: float = 0.01) -> dict:
    """Standard facade: standard historical VaR as a JSON-serializable dict.

    Parameters:
    returns: 1-D array-like of historical returns (fractions).
    alpha (float): Tail probability in (0, 1), e.g. 0.01.

    Returns:
    dict: {"method", "alpha", "n", "var"} with "var" the positive loss
    fraction.
    """
    returns = np.asarray(returns, dtype=float).ravel()
    if returns.size == 0:
        raise ValueError("returns must contain at least one observation")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    var = calculate_historical_var(returns, float(alpha))
    return {
        "method": "historical",
        "alpha": float(alpha),
        "n": int(returns.size),
        "var": float(var),
    }


if __name__ == "__main__":
    np.random.seed(42)

    # Generate a mock historical dataset of 1000 days that is deliberately NOT normal
    # (Using a Student-t distribution with 3 degrees of freedom to simulate heavy tails)
    historical_data = np.random.standard_t(df=3, size=1000) * 0.01

    # Calculate 1% Historical VaR
    hist_var = calculate_historical_var(historical_data, alpha=0.01)

    print(f"Number of historical scenarios: {len(historical_data)}")
    print(f"1% Historical VaR Estimate: {hist_var:.2%}")
