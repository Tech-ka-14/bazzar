"""Autocorrelation of credit spread changes (iTraxx Europe).

The sample autocorrelation of first differences of the iTraxx Europe 5-year
index reveals a strong positive autocorrelation in credit-spread changes,
motivating autocorrelation-adjusted VaR scaling.
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.2.12,
Figure IV.2.22.
"""

import numpy as np
import pandas as pd


def analyze_credit_spread_autocorrelation(spread_series: pd.Series, max_lags: int = 10):
    """
    Analyzes the autocorrelation of the first differences (changes) of a credit spread series.
    Mimics the analysis of the iTraxx Europe 5-year index presented in Section IV.2.12.

    Parameters:
    spread_series (pd.Series): Time series of credit spreads (e.g., in basis points).
    max_lags (int): Number of lags to evaluate.

    Returns:
    tuple: (dict of autocorrelations, the first difference series)
    """
    # 1. Calculate the first differences (daily changes)
    spread_changes = spread_series.diff().dropna()

    # 2. Calculate the autocorrelations
    autocorrelations = {}
    for lag in range(1, max_lags + 1):
        # Using pandas built-in autocorr which calculates the Pearson correlation
        # of the series with its lagged self
        autocorrelations[f"Lag {lag}"] = spread_changes.autocorr(lag=lag)

    return autocorrelations, spread_changes


def compute(spread_series, max_lags: int = 10) -> dict:
    """Standard facade: credit-spread change autocorrelations as a JSON dict.

    Parameters:
    spread_series: 1-D array-like of credit-spread levels (at least
    max_lags + 2 observations).
    max_lags (int): Number of lags to evaluate (>= 1).

    Returns:
    dict: {"n_changes", "lag_1_autocorrelation", "autocorrelations"} where
    autocorrelations maps "lag_<k>" to the sample autocorrelation of the
    spread changes.
    """
    series = pd.Series(np.asarray(spread_series, dtype=float).ravel())
    max_lags = int(max_lags)
    if max_lags < 1:
        raise ValueError("max_lags must be at least 1")
    if series.size < max_lags + 2:
        raise ValueError("spread_series is too short for the requested lags")

    autocorrelations, changes = analyze_credit_spread_autocorrelation(series, max_lags)
    result = {"n_changes": int(changes.size), "lag_1_autocorrelation": None}
    for lag in range(1, max_lags + 1):
        key = f"lag_{lag}"
        value = autocorrelations[f"Lag {lag}"]
        result[key] = None if pd.isna(value) else float(value)
        if lag == 1:
            result["lag_1_autocorrelation"] = result[key]
    return result


# --- Demonstration of Autocorrelation in Credit Spreads ---


def _main():
    # Setup Mock iTraxx Europe 5-year Index Data
    # Highly autocorrelated data (simulated random walk with drift and mean reversion)
    np.random.seed(42)
    n_days = 1000

    # Generate a mock spread series that trends and has autocorrelated changes
    mock_changes = np.random.normal(0, 2.0, n_days)
    for i in range(1, n_days):
        # Introduce strong AR(1) behavior to mimic credit spreads
        mock_changes[i] += 0.65 * mock_changes[i - 1]

    mock_spreads = pd.Series(np.cumsum(mock_changes) + 50)  # Base of 50 bps

    # Execute Analysis
    autocorr_results, changes = analyze_credit_spread_autocorrelation(mock_spreads)

    print("--- Credit Spread Changes Autocorrelation (Mock Data) ---")
    for lag, rho in autocorr_results.items():
        print(f"{lag}: {rho:.4f}")

    print("\nInterpretation:")
    print("Credit spreads exhibit strong positive autocorrelation in their daily changes.")
    print(
        "Because credit markets trend significantly (unlike i.i.d equity markets), using the square-root-of-time rule for VaR severely underestimates the true risk over longer horizons."
    )


if __name__ == "__main__":
    _main()
