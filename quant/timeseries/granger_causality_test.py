"""Granger causality test.

Bivariate Granger causality: whether lagged X values jointly help predict Y
(F-test on the restricted vs unrestricted autoregressive regressions).
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests


def test_granger_causality(y_series, x_series, max_lags=5):
    """
    Performs a Granger Causality test to see if time series X causes time series Y.
    """
    # Combine the two series into a single DataFrame
    data = pd.concat([y_series, x_series], axis=1)
    data.columns = ["Y", "X"]

    # Perform the Granger Causality test
    # It returns a dictionary of test results for each lag
    gc_results = grangercausalitytests(data[["Y", "X"]], maxlag=max_lags, verbose=False)

    # Extract the p-values for the F-test
    f_test_p_values = [gc_results[lag][0]["ssr_ftest"][1] for lag in range(1, max_lags + 1)]

    # Determine the optimal lag based on the lowest p-value
    optimal_lag = np.argmin(f_test_p_values) + 1
    min_p_value = min(f_test_p_values)

    return {"optimal_lag": optimal_lag, "min_p_value": min_p_value, "causal": min_p_value < 0.05}


def compute(data, x_series=None, max_lags: int = 5) -> dict:
    """Standard facade: bivariate Granger causality as a JSON dict.

    Parameters:
    data: 1-D array-like of the target series Y.
    x_series: 1-D array-like of the candidate causal series X, same length.
    max_lags (int): Maximum lag order to test (>= 1).

    Returns:
    dict: {"optimal_lag", "min_p_value", "causal_at_5pct"} with plain
    floats/ints/bools.
    """
    if x_series is None:
        raise ValueError("x_series is required")
    y = pd.Series(np.asarray(data, dtype=float).ravel())
    x = pd.Series(np.asarray(x_series, dtype=float).ravel())
    max_lags = int(max_lags)
    if max_lags < 1:
        raise ValueError("max_lags must be at least 1")
    if y.size != x.size or y.size < 4 * max_lags + 5:
        raise ValueError("series must have equal length and enough observations for max_lags")

    results = test_granger_causality(y, x, max_lags=max_lags)
    return {
        "optimal_lag": int(results["optimal_lag"]),
        "min_p_value": float(results["min_p_value"]),
        "causal_at_5pct": bool(results["causal"]),
    }


# Example usage
# gc_results = test_granger_causality(stock_returns, bond_yields, max_lags=5)
