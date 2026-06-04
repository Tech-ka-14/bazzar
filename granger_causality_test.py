import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests

def test_granger_causality(data_df, target_col, predictor_col, max_lags=5):
    """
    Tests if predictor_col Granger-causes target_col. 
    Null Hypothesis (H0): Predictor does NOT Granger-cause Target.
    """
    # The statsmodels function expects a 2D array where the FIRST column is the target 
    # and the SECOND column is the predictor.
    test_data = data_df[[target_col, predictor_col]]
    
    # Run the test
    print(f"Testing if {predictor_col} Granger-causes {target_col}...")
    
    # verbose=False suppresses the raw console output so we can parse the dictionary cleanly
    gc_results = grangercausalitytests(test_data, maxlag=max_lags, verbose=False)
    
    summary = []
    for lag in range(1, max_lags + 1):
        # Extract the SSR based F-test p-value for the specific lag
        f_test_p_value = gc_results[lag][0]['ssr_ftest'][1]
        
        summary.append({
            "Lag": lag,
            "F-Test p-value": f_test_p_value,
            "Reject H0 (Predicts Target)": f_test_p_value < 0.05
        })
        
    return pd.DataFrame(summary)

# Example Usage:
# Assuming 'market_data' is a DataFrame containing 'NIFTY_Returns' and 'INR_USD_Returns'
# causality_df = test_granger_causality(market_data, target_col='NIFTY_Returns', predictor_col='INR_USD_Returns')