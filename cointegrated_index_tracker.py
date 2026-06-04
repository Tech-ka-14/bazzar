import numpy as np
import pandas as pd
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
    raw_weights = tracking_model.params.drop('const')
    
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
        "Model R-Squared": tracking_model.rsquared
    }

# Example Usage:
# Assume 'sp500' is a Series and 'top_20_stocks' is a DataFrame of 20 asset prices
# tracking_results = build_cointegrated_tracker(benchmark_prices=sp500, component_prices=top_20_stocks)
# print(tracking_results["Optimal Weights"])