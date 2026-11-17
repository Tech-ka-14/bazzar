"""Augmented Dickey-Fuller stationarity test.

ADF unit-root test on a time series; the series is deemed stationary when the
test p-value falls below the chosen significance level.
"""

from statsmodels.tsa.stattools import adfuller


def test_stationarity(time_series, significance_level=0.05):
    """
    Performs the Augmented Dickey-Fuller test to check for stationarity.
    """
    # Perform the ADF test
    adf_result = adfuller(time_series, autolag="AIC")

    test_statistic = adf_result[0]
    p_value = adf_result[1]
    critical_values = adf_result[4]

    # Check against the significance level
    is_stationary = p_value < significance_level

    return {
        "Test Statistic": test_statistic,
        "p-value": p_value,
        "Critical Values": critical_values,
        "Is Stationary": is_stationary,
    }


def compute(time_series, significance_level: float = 0.05) -> dict:
    """Standard facade: ADF stationarity test as a JSON-serializable dict.

    Parameters:
    time_series: 1-D array-like of observations (e.g. a price series).
    significance_level (float): Test size in (0, 1); the series is reported
    stationary when the ADF p-value is below it.

    Returns:
    dict: {"test_statistic", "p_value", "critical_values",
    "is_stationary"} with plain floats/bools.
    """
    if not 0.0 < float(significance_level) < 1.0:
        raise ValueError("significance_level must be in the open interval (0, 1)")

    result = test_stationarity(time_series, float(significance_level))
    return {
        "test_statistic": float(result["Test Statistic"]),
        "p_value": float(result["p-value"]),
        "critical_values": {str(k): float(v) for k, v in result["Critical Values"].items()},
        "is_stationary": bool(result["Is Stationary"]),
    }


# Example usage (assuming 'prices' is a Pandas Series of asset prices)
# result = test_stationarity(prices)
# print("Stationary:" if result["Is Stationary"] else "Non-Stationary")
