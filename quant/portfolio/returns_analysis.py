"""Return series analysis.

Percentage returns R_t = (P_t - P_{t-1}) / P_{t-1} and log returns
ln(P_t / P_{t-1}); the h-period log return is the sum of h consecutive
one-period log returns, and a linear portfolio return is the weighted sum
of asset returns.
"""

import numpy as np
import pandas as pd


def calculate_returns(prices_series):
    """
    Calculates 1-period percentage returns and log returns for an asset.
    """
    df = pd.DataFrame(prices_series, columns=["Price"])

    # 1. Percentage Return: (P_t - P_{t-1}) / P_{t-1}
    df["Pct_Return"] = df["Price"].pct_change()

    # 2. Log Return: ln(P_t / P_{t-1})
    df["Log_Return"] = np.log(df["Price"] / df["Price"].shift(1))

    return df


def multi_period_log_return(log_returns, h_periods):
    """
    Calculates the h-period log return.
    The h-period log return is the sum of h consecutive one-period log returns.
    """
    # Using rolling sum to aggregate h periods
    return log_returns.rolling(window=h_periods).sum()


def linear_portfolio_return(weights, asset_returns):
    """
    Calculates the return of a linear portfolio as a weighted sum of asset returns.
    R = sum(w_i * R_i)

    :param weights: Array-like of portfolio weights
    :param asset_returns: Array-like of corresponding asset returns
    """
    return np.dot(weights, asset_returns)


def compute(prices, h_periods: int = None) -> dict:
    """Standard facade: return series analysis as a JSON-serializable dict.

    Parameters:
    prices: 1-D array-like of asset prices (positive), at least two values.
    h_periods (int, optional): When supplied, the h-period aggregated log
    return over the whole sample is also reported.

    Returns:
    dict: {"n", "pct_returns", "log_returns", "total_pct_return",
    "total_log_return", "h_periods", "h_period_log_return"}; the first
    element of pct_returns/log_returns is None. h_period entries are None
    unless h_periods is supplied.
    """
    prices = np.asarray(prices, dtype=float).ravel()
    if prices.size < 2:
        raise ValueError("prices must contain at least two observations")
    if (prices <= 0).any():
        raise ValueError("prices must be strictly positive")

    df = calculate_returns(pd.Series(prices))

    def _series(column):
        return [None if pd.isna(v) else float(v) for v in df[column]]

    result = {
        "n": int(prices.size),
        "pct_returns": _series("Pct_Return"),
        "log_returns": _series("Log_Return"),
        "total_pct_return": float(prices[-1] / prices[0] - 1.0),
        "total_log_return": float(np.log(prices[-1] / prices[0])),
        "h_periods": None,
        "h_period_log_return": None,
    }
    if h_periods is not None:
        h_periods = int(h_periods)
        if not 1 <= h_periods < prices.size:
            raise ValueError("h_periods must be between 1 and len(prices) - 1")
        aggregated = multi_period_log_return(df["Log_Return"], h_periods).dropna()
        result["h_periods"] = h_periods
        result["h_period_log_return"] = float(aggregated.iloc[-1])
    return result


# --- Testing the methods ---
if __name__ == "__main__":
    # Hypothetical price series
    prices = [100, 105, 102, 108, 110]
    returns_df = calculate_returns(prices)

    # Calculate a 2-period log return
    returns_df["2_Period_Log_Return"] = multi_period_log_return(returns_df["Log_Return"], 2)

    print("--- Individual Asset Returns ---")
    print(returns_df.round(4))

    # Portfolio Return Example (Example I.1.7 concept)
    # 60% in Asset 1 (return 25%), 40% in Asset 2 (return 150%)
    port_weights = np.array([0.60, 0.40])
    asset_rets = np.array([0.25, 1.50])

    port_return = linear_portfolio_return(port_weights, asset_rets)
    print(f"\nPortfolio Return: {port_return:.2%}")
