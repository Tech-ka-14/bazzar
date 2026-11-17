"""Profit and loss (P&L) calculations.

Backward-looking P&L: P_t - P_{t-1} (realized change over the last period);
forward-looking P&L: P_{t+1} - P_t (next period's change, known only ex post
for historical series).
"""

import pandas as pd


def calculate_pnl(prices_data, value_column="Portfolio_Value"):
    """
    Calculates both backward-looking (historical) and forward-looking (forecast)
    Profit and Loss (P&L) for a given time series of portfolio values or asset prices.

    :param prices_data: Dictionary or DataFrame containing the price data over time.
    :param value_column: The name of the column containing the values to difference.
    :return: Pandas DataFrame with the original values and calculated P&L.
    """
    df = pd.DataFrame(prices_data)

    if value_column not in df.columns:
        raise ValueError(f"Column '{value_column}' not found in the provided data.")

    # 1. Backward-Looking P&L: P_t - P_{t-1}
    # Using pandas .diff() which defaults to periods=1 (current minus previous)
    df["PnL_Backward"] = df[value_column].diff()

    # 2. Forward-Looking P&L: P_{t+1} - P_t
    # We achieve this by shifting the data backward by 1 period and subtracting the current
    df["PnL_Forward"] = df[value_column].shift(-1) - df[value_column]

    return df


def compute(prices_data, value_column: str = "Portfolio_Value") -> dict:
    """Standard facade: P&L series summary as a JSON-serializable dict.

    Parameters:
    prices_data: Dict of column lists (or pandas DataFrame) containing a
    value/price column.
    value_column (str): Name of the column to difference.

    Returns:
    dict: {"value_column", "n_periods", "backward_pnl", "forward_pnl",
    "total_backward_pnl"}; the first backward and last forward entries are
    None (undefined), matching pandas diff/shift semantics.
    """
    df = calculate_pnl(prices_data, value_column=value_column)

    def _series(column):
        return [None if pd.isna(v) else float(v) for v in df[column]]

    return {
        "value_column": str(value_column),
        "n_periods": int(len(df)),
        "backward_pnl": _series("PnL_Backward"),
        "forward_pnl": _series("PnL_Forward"),
        "total_backward_pnl": float(df["PnL_Backward"].sum()),
    }


# --- Testing with a hypothetical portfolio value sequence ---
if __name__ == "__main__":
    # Hypothetical portfolio values over 5 days
    historical_data = {
        "Day": [1, 2, 3, 4, 5],
        "Portfolio_Value": [100000, 102000, 99000, 105000, 106500],
    }

    # Run the P&L analysis
    pnl_df = calculate_pnl(historical_data, value_column="Portfolio_Value")

    # Format output for clean reading
    pd.options.display.float_format = "{:,.2f}".format

    print("--- Profit and Loss Analysis ---")
    print(pnl_df[["Day", "Portfolio_Value", "PnL_Backward", "PnL_Forward"]])
