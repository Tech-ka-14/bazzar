"""Historical simulation Value at Risk.

VaR at confidence level c is the negative of the empirical alpha-quantile
(alpha = 1 - c) of the historical return distribution, using linear
interpolation between discrete nodes (``numpy.quantile(..., method="linear")``).
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.1.2.
"""

import numpy as np


def calculate_empirical_historical_var(
    historical_returns: np.ndarray, portfolio_value: float, confidence_level: float
):
    """
    Calculates Historical Simulation VaR using empirical quantiles and interpolation.

    Parameters:
    historical_returns (np.ndarray): An array of historically simulated h-day returns.
    portfolio_value (float): The current nominal value of the portfolio.
    confidence_level (float): The target confidence level (e.g., 0.99 for 1% VaR).

    Returns:
    tuple: (VaR percentage, VaR in value terms)
    """
    alpha = 1.0 - confidence_level

    # Sort the returns to build the empirical cumulative distribution
    sorted_returns = np.sort(historical_returns)

    # Find the alpha quantile.
    # By default, numpy's quantile uses linear interpolation between discrete historical nodes.
    var_percentile = np.quantile(sorted_returns, alpha, method="linear")

    # VaR is strictly defined as the negative of the loss quantile
    var_percentage = -var_percentile
    var_value = var_percentage * portfolio_value

    return var_percentage, var_value


def compute(returns, confidence: float = 0.99, portfolio_value: float = 1.0) -> dict:
    """Standard facade: historical simulation VaR as a JSON-serializable dict.

    Parameters:
    returns: 1-D array-like of historical returns (fractions, e.g. -0.02).
    confidence (float): Confidence level in (0, 1), e.g. 0.99.
    portfolio_value (float): Nominal portfolio value for the monetary VaR.

    Returns:
    dict: {"method", "confidence", "n", "var", "var_value"} where "var" is
    the positive loss fraction and "var_value" the monetary loss.
    """
    returns = np.asarray(returns, dtype=float).ravel()
    if returns.size == 0:
        raise ValueError("returns must contain at least one observation")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in the open interval (0, 1)")

    var_pct, var_val = calculate_empirical_historical_var(
        returns, float(portfolio_value), float(confidence)
    )
    return {
        "method": "historical",
        "confidence": float(confidence),
        "n": int(returns.size),
        "var": float(var_pct),
        "var_value": float(var_val),
    }


if __name__ == "__main__":
    # Mock dataset representing a 1000-day historical simulation
    np.random.seed(42)
    # Creating a fat-tailed distribution (Student-t) to emphasize non-normality
    historical_sim_returns = np.random.standard_t(df=4, size=1000) * 0.015

    current_portfolio_value = 1_000_000
    conf = 0.99  # 99% Confidence (1% VaR)

    var_pct, var_val = calculate_empirical_historical_var(
        historical_sim_returns, current_portfolio_value, conf
    )

    print("--- Historical Simulation VaR ---")
    print(f"Number of Simulated Scenarios: {len(historical_sim_returns)}")
    print(f"1% Historical VaR (Percentage): {var_pct:.4%}")
    print(f"1% Historical VaR (Value): ${var_val:,.2f}")
