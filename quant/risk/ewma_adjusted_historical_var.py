"""EWMA volatility-adjusted historical P&L scenarios.

Historical P&L scenarios are rescaled by the ratio of the current EWMA
volatility to the historical EWMA volatility state, so that scenarios
reflect the current volatility regime.
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.3.4
(volatility-adjusted historical simulation).
"""

import numpy as np


def calculate_ewma_adjusted_pnl(pnl_series: np.ndarray, lambda_ewma: float = 0.90) -> np.ndarray:
    """
    Applies EWMA to extract the volatility of the P&L series and scales
    historical P&L to reflect the most recent 'current' volatility state.
    """
    n = len(pnl_series)
    ewma_var = np.zeros(n)

    # Initialize with the sample variance
    ewma_var[0] = np.var(pnl_series)

    # Recursive EWMA variance calculation
    for t in range(1, n):
        ewma_var[t] = (1 - lambda_ewma) * (pnl_series[t - 1] ** 2) + (lambda_ewma * ewma_var[t - 1])

    ewma_vol = np.sqrt(ewma_var)
    current_vol = ewma_vol[-1]  # The most recent volatility state

    # Scale historical P&L scenarios by the ratio of current vol to historical vol
    adjusted_pnl_series = pnl_series * (current_vol / ewma_vol)

    return adjusted_pnl_series


# Example Implementation using mock data


def compute(
    pnl_series, lambda_ewma: float = 0.90, alpha: float = 0.01, horizon_days: int = 10
) -> dict:
    """Standard facade: EWMA-adjusted historical VaR as a JSON dict.

    Parameters:
    pnl_series: 1-D array-like of historical daily P&L scenarios.
    lambda_ewma (float): EWMA smoothing constant in (0, 1).
    alpha (float): Tail probability in (0, 1), e.g. 0.01.
    horizon_days (int): Risk horizon in days (square-root scaling).

    Returns:
    dict: {"method", "alpha", "horizon_days", "n", "var",
    "var_unadjusted"} with positive losses.
    """
    pnl = np.asarray(pnl_series, dtype=float).ravel()
    if pnl.size < 2:
        raise ValueError("pnl_series must contain at least two observations")
    if not 0.0 < lambda_ewma < 1.0:
        raise ValueError("lambda_ewma must be in the open interval (0, 1)")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    adjusted = calculate_ewma_adjusted_pnl(pnl, float(lambda_ewma))
    var_adj = -np.quantile(adjusted, alpha) * np.sqrt(int(horizon_days))
    var_raw = -np.quantile(pnl, alpha) * np.sqrt(int(horizon_days))
    return {
        "method": "ewma_adjusted_historical",
        "alpha": float(alpha),
        "horizon_days": int(horizon_days),
        "n": int(pnl.size),
        "var": float(var_adj),
        "var_unadjusted": float(var_raw),
    }


if __name__ == "__main__":
    mock_historical_rates = np.random.standard_normal((250, 5)) * 0.0005  # daily rate moves
    mock_pv01 = np.full(5, 1000.0)  # PV01 per position
    raw_simulated_pnl = -np.dot(mock_historical_rates, mock_pv01)

    # Apply EWMA adjustment (using lambda 0.90 as mentioned in the case study)
    adjusted_pnl = calculate_ewma_adjusted_pnl(raw_simulated_pnl, lambda_ewma=0.90)

    # Calculate unadjusted vs adjusted VaR
    unadjusted_var = -np.quantile(raw_simulated_pnl, 0.01) * np.sqrt(10)
    adjusted_var = -np.quantile(adjusted_pnl, 0.01) * np.sqrt(10)

    print(f"Unadjusted 1% 10-Day VaR: ${unadjusted_var:,.2f}")
    print(f"EWMA Adjusted 1% 10-Day VaR: ${adjusted_var:,.2f}")
