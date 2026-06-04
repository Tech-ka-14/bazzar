import pandas as pd
from statsmodels.tsa.stattools import adfuller

def test_stationarity(time_series, significance_level=0.05):
    """
    Performs the Augmented Dickey-Fuller test to check for stationarity.
    """
    # Perform the ADF test
    adf_result = adfuller(time_series, autolag='AIC')
    
    test_statistic = adf_result[0]
    p_value = adf_result[1]
    critical_values = adf_result[4]
    
    # Check against the significance level
    is_stationary = p_value < significance_level
    
    return {
        "Test Statistic": test_statistic,
        "p-value": p_value,
        "Critical Values": critical_values,
        "Is Stationary": is_stationary
    }

# Example usage (assuming 'prices' is a Pandas Series of asset prices)
# result = test_stationarity(prices)
# print("Stationary:" if result["Is Stationary"] else "Non-Stationary")