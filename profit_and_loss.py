import pandas as pd

def calculate_pnl(prices_data, value_column='Portfolio_Value'):
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
    df['PnL_Backward'] = df[value_column].diff()
    
    # 2. Forward-Looking P&L: P_{t+1} - P_t
    # We achieve this by shifting the data backward by 1 period and subtracting the current
    df['PnL_Forward'] = df[value_column].shift(-1) - df[value_column]
    
    return df

# --- Testing with a hypothetical portfolio value sequence ---
if __name__ == "__main__":
    # Hypothetical portfolio values over 5 days
    historical_data = {
        'Day': [1, 2, 3, 4, 5],
        'Portfolio_Value': [100000, 102000, 99000, 105000, 106500]
    }
    
    # Run the P&L analysis
    pnl_df = calculate_pnl(historical_data, value_column='Portfolio_Value')
    
    # Format output for clean reading
    pd.options.display.float_format = '{:,.2f}'.format
    
    print("--- Profit and Loss Analysis ---")
    print(pnl_df[['Day', 'Portfolio_Value', 'PnL_Backward', 'PnL_Forward']])