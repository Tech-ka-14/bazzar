import pandas as pd
import numpy as np

def calculate_returns(prices_series):
    """
    Calculates 1-period percentage returns and log returns for an asset.
    """
    df = pd.DataFrame(prices_series, columns=['Price'])
    
    # 1. Percentage Return: (P_t - P_{t-1}) / P_{t-1}
    df['Pct_Return'] = df['Price'].pct_change()
    
    # 2. Log Return: ln(P_t / P_{t-1})
    df['Log_Return'] = np.log(df['Price'] / df['Price'].shift(1))
    
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

# --- Testing the methods ---
if __name__ == "__main__":
    # Hypothetical price series
    prices = [100, 105, 102, 108, 110]
    returns_df = calculate_returns(prices)
    
    # Calculate a 2-period log return
    returns_df['2_Period_Log_Return'] = multi_period_log_return(returns_df['Log_Return'], 2)
    
    print("--- Individual Asset Returns ---")
    print(returns_df.round(4))
    
    # Portfolio Return Example (Example I.1.7 concept)
    # 60% in Asset 1 (return 25%), 40% in Asset 2 (return 150%)
    port_weights = np.array([0.60, 0.40])
    asset_rets = np.array([0.25, 1.50])
    
    port_return = linear_portfolio_return(port_weights, asset_rets)
    print(f"\nPortfolio Return: {port_return:.2%}")