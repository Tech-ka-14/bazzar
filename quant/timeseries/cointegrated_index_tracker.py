"""Cointegration-based index tracking portfolio.

Engle-Granger regression of the log benchmark price on log component prices;
the normalized regression coefficients are the tracking weights, and the ADF
test on the residual spread checks that the tracker is cointegrated with the
benchmark (no drift).
"""

import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller


def build_cointegrated_tracker(benchmark_prices, component_prices):
    """
    Constructs an index-tracking portfolio using cointegration on log-prices.

    benchmark_prices: Pandas Series of the Index prices.
    component_prices: Pandas DataFrame of the selected subset of stock prices.
    """
    # 1. Transform to log-prices to capture geometric growth relationships
    log_bench = np.log(benchmark_prices)
    log_comps = np.log(component_prices)

    # 2. Engle-Granger Cointegration Regression
    # Regress log(Benchmark) on log(Components)
    X = sm.add_constant(log_comps)
    tracking_model = sm.OLS(log_bench, X).fit()

    # 3. Extract and normalize the portfolio weights (betas)
    # Drop the constant to isolate the stock coefficients
    raw_weights = tracking_model.params.drop("const")

    # Normalize weights so capital allocation sums to 1 (100%)
    normalized_weights = raw_weights / raw_weights.sum()

    # 4. Construct the Tracking Portfolio's synthetic log-price
    # P_track = w1*P1 + w2*P2 ... wk*Pk
    portfolio_log_prices = log_comps.dot(normalized_weights)

    # 5. Calculate the Tracking Error (Spread)
    tracking_spread = log_bench - portfolio_log_prices

    # 6. Test the spread for stationarity (Does the portfolio drift?)
    adf_result = adfuller(tracking_spread)
    is_cointegrated = adf_result[1] < 0.05

    return {
        "Optimal Weights": normalized_weights.to_dict(),
        "Tracking Spread Stationarity (ADF p-value)": adf_result[1],
        "Mean-Reverting (No Drift)": is_cointegrated,
        "Model R-Squared": tracking_model.rsquared,
    }


def compute(benchmark_prices, component_prices) -> dict:
    """Standard facade: cointegrated tracker weights as a JSON dict.

    Parameters:
    benchmark_prices: 1-D array-like of benchmark index prices (positive).
    component_prices: pandas DataFrame (or dict of equal-length column lists)
    of component asset prices over the same dates.

    Returns:
    dict: {"optimal_weights", "adf_p_value", "is_cointegrated",
    "r_squared"}; weights are normalized to sum to 1.
    """
    import pandas as pd

    if isinstance(benchmark_prices, pd.Series):
        benchmark_prices = benchmark_prices.astype(float).reset_index(drop=True)
    else:
        benchmark_prices = pd.Series(np.asarray(benchmark_prices, dtype=float).ravel())
    if not isinstance(component_prices, pd.DataFrame):
        component_prices = pd.DataFrame(component_prices)
    if len(benchmark_prices) != len(component_prices):
        raise ValueError("benchmark_prices and component_prices must have equal length")
    if (benchmark_prices <= 0).any() or (component_prices <= 0).any().any():
        raise ValueError("prices must be strictly positive to take logarithms")

    results = build_cointegrated_tracker(benchmark_prices, component_prices)
    return {
        "optimal_weights": {str(k): float(v) for k, v in results["Optimal Weights"].items()},
        "adf_p_value": float(results["Tracking Spread Stationarity (ADF p-value)"]),
        "is_cointegrated": bool(results["Mean-Reverting (No Drift)"]),
        "r_squared": float(results["Model R-Squared"]),
    }


# Example Usage:
# Assume 'sp500' is a Series and 'top_20_stocks' is a DataFrame of 20 asset prices
# tracking_results = build_cointegrated_tracker(benchmark_prices=sp500, component_prices=top_20_stocks)
# print(tracking_results["Optimal Weights"])
