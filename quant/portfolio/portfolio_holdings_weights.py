"""Portfolio holdings, values and weights over time.

For constant holdings n_i, the portfolio value is P_t = sum_i n_i p_{it}
and the portfolio weights are w_{it} = n_i p_{it} / P_t (Example I.1.5,
Alexander 2008).
"""

import pandas as pd


def analyze_portfolio(holdings, prices_data):
    """
    Calculates portfolio values and weights over time for a portfolio
    with constant holdings (no rebalancing).

    :param holdings: Dictionary of asset holdings {asset_name: quantity}
    :param prices_data: Dictionary of prices over time (can include a time/date column)
    :return: Pandas DataFrame containing prices, values, total portfolio value, and weights
    """
    # Create a DataFrame from the price data
    df = pd.DataFrame(prices_data)

    # Optional: Set 'Year' or 'Date' as the index if it exists in the data
    if "Year" in df.columns:
        df.set_index("Year", inplace=True)

    # 1. Calculate individual asset values: n_i * p_{it}
    value_columns = []
    for asset, quantity in holdings.items():
        val_col_name = f"Value_{asset}"
        df[val_col_name] = df[asset] * quantity
        value_columns.append(val_col_name)

    # 2. Calculate total portfolio value: P_t = sum(n_i * p_{it})
    df["Portfolio_Value"] = df[value_columns].sum(axis=1)

    # 3. Calculate portfolio weights: w_{it} = (n_i * p_{it}) / P_t
    for asset in holdings.keys():
        weight_col_name = f"Weight_{asset}"
        df[weight_col_name] = df[f"Value_{asset}"] / df["Portfolio_Value"]

    return df


def compute(holdings, prices_data) -> dict:
    """Standard facade: holdings-based weights summary as a JSON dict.

    Parameters:
    holdings: Dict of {asset_name: quantity} (constant holdings).
    prices_data: Dict of price columns over time (or pandas DataFrame); must
    contain one column per held asset.

    Returns:
    dict: {"n_periods", "portfolio_values", "final_weights",
    "final_value"} with the portfolio value series, the latest weights per
    asset and the latest total value.
    """
    if not isinstance(holdings, dict) or not holdings:
        raise ValueError("holdings must be a non-empty dict of {asset: quantity}")
    df = analyze_portfolio(holdings, prices_data)

    final_weights = {str(asset): float(df[f"Weight_{asset}"].iloc[-1]) for asset in holdings}
    return {
        "n_periods": int(len(df)),
        "portfolio_values": [float(v) for v in df["Portfolio_Value"]],
        "final_weights": final_weights,
        "final_value": float(df["Portfolio_Value"].iloc[-1]),
    }


# --- Testing with Example I.1.5 from the text ---
if __name__ == "__main__":
    # Define the constant holdings (n_i)
    initial_holdings = {"Asset_1": 600, "Asset_2": 200}

    # Define the asset prices over time (p_{it})
    historical_prices = {
        "Year": [2003, 2004, 2005, 2006],
        "Asset_1": [100, 125, 80, 120],
        "Asset_2": [200, 500, 250, 400],
    }

    # Run the analysis
    portfolio_df = analyze_portfolio(initial_holdings, historical_prices)

    # Format the output for readability (displaying weights to 3 decimal places)
    pd.options.display.float_format = "{:.3f}".format

    print("--- Portfolio Analysis (Example I.1.5) ---")
    # Rearrange columns to perfectly match Table I.1.2 in the text
    display_columns = [
        "Asset_1",
        "Asset_2",
        "Weight_Asset_1",
        "Weight_Asset_2",
        "Value_Asset_1",
        "Value_Asset_2",
        "Portfolio_Value",
    ]
    print(portfolio_df[display_columns])
