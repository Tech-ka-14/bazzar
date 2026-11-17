"""Normal linear VaR for a cash equity portfolio.

Portfolio VaR from position weights and an h-day covariance matrix, with
and without the expected-drift adjustment.
Reference: Alexander (2008), Market Risk Analysis IV, Equation IV.2.44,
Example IV.2.11.
"""

import numpy as np
from scipy.stats import norm


def calculate_equity_cash_var(
    weights: np.ndarray,
    cov_matrix_h: np.ndarray,
    expected_returns_h: np.ndarray,
    portfolio_value: float,
    alpha: float = 0.01,
) -> tuple:
    """
    Calculates the Normal Linear VaR for a cash equity portfolio, both with
    and without the expected drift adjustment (Equation IV.2.44).
    """
    # 1. Calculate Portfolio Volatility (sqrt(w' * V * w))
    portfolio_variance = weights.T @ cov_matrix_h @ weights
    portfolio_volatility = np.sqrt(portfolio_variance)

    # 2. Calculate the Expected Portfolio Return (w' * E(x))
    expected_portfolio_return = weights.T @ expected_returns_h

    # 3. Base VaR (Zero Mean Assumption)
    critical_value = norm.ppf(1 - alpha)
    var_zero_mean_pct = critical_value * portfolio_volatility
    var_zero_mean_val = var_zero_mean_pct * portfolio_value

    # 4. Drift Adjusted VaR
    var_adjusted_pct = var_zero_mean_pct - expected_portfolio_return
    var_adjusted_val = var_adjusted_pct * portfolio_value

    return var_zero_mean_val, var_adjusted_val


# Example IV.2.11: VaR for Cash Equity Positions (10-day horizon)
# Positions in millions of Euros


def compute(
    weights, cov_matrix_h, expected_returns_h, portfolio_value: float = 1.0, alpha: float = 0.01
) -> dict:
    """Standard facade: cash equity VaR as a JSON-serializable dict.

    Parameters:
    weights: 1-D array-like of position weights (or relative exposures).
    cov_matrix_h: Square h-day covariance matrix matching len(weights).
    expected_returns_h: 1-D array-like of h-day expected returns.
    portfolio_value (float): Nominal portfolio value.
    alpha (float): Tail probability in (0, 1), e.g. 0.01.

    Returns:
    dict: {"method", "alpha", "portfolio_value", "var",
    "var_drift_adjusted"} with positive monetary losses.
    """
    weights = np.asarray(weights, dtype=float).ravel()
    cov = np.asarray(cov_matrix_h, dtype=float)
    mu = np.asarray(expected_returns_h, dtype=float).ravel()
    if weights.size == 0:
        raise ValueError("weights must contain at least one entry")
    if cov.shape != (weights.size, weights.size):
        raise ValueError("cov_matrix_h must be square with size len(weights)")
    if mu.size != weights.size:
        raise ValueError("expected_returns_h must have the same length as weights")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    var_base, var_adj = calculate_equity_cash_var(
        weights, cov, mu, float(portfolio_value), float(alpha)
    )
    return {
        "method": "normal_linear",
        "alpha": float(alpha),
        "portfolio_value": float(portfolio_value),
        "var": float(var_base),
        "var_drift_adjusted": float(var_adj),
    }


if __name__ == "__main__":
    positions = np.array([4.0, -5.0, 1.0])
    total_portfolio_value = np.sum(np.abs(positions))  # Gross Exposure basis

    # 10-day Expected Returns
    expected_ret_10d = np.array([0.004, 0.0008, 0.002])

    # 10-day Covariance Matrix
    cov_10d = np.array(
        [[0.0016, 0.00064, 0.0006], [0.00064, 0.0004, 0.00018], [0.0006, 0.00018, 0.0009]]
    )

    var_base, var_adj = calculate_equity_cash_var(
        positions, cov_10d, expected_ret_10d, total_portfolio_value=1.0, alpha=0.01
    )

    print(f"1% 10-day VaR (Zero Drift): €{var_base:,.0f}")
    print(f"1% 10-day VaR (Drift Adjusted): €{var_adj:,.0f}")
