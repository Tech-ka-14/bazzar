"""Capital Market Line (CML).

CML expected return: E[R_p] = r_f + Sharpe_market * sigma_p, where
Sharpe_market = (E[R_m] - r_f) / sigma_m is the slope of the CML
(Example I.6.10, Alexander 2008).
"""


def calculate_sharpe_ratio(expected_return, risk_free_rate, volatility):
    """
    Calculates the Sharpe ratio for a portfolio.
    """
    return (expected_return - risk_free_rate) / volatility


def capital_market_line(risk_free_rate, sharpe_ratio, target_volatility):
    """
    Calculates the expected return of a portfolio on the Capital Market Line (CML)
    given a target level of risk (volatility).
    """
    return risk_free_rate + (sharpe_ratio * target_volatility)


def compute(
    risk_free_rate: float,
    market_expected_return: float,
    market_volatility: float,
    target_volatility: float,
) -> dict:
    """Standard facade: CML expected return as a JSON-serializable dict.

    Parameters:
    risk_free_rate (float): Risk-free rate (fraction).
    market_expected_return (float): Expected market return (fraction).
    market_volatility (float): Market volatility (fraction), positive.
    target_volatility (float): Target portfolio volatility, non-negative.

    Returns:
    dict: {"market_sharpe_ratio", "cml_expected_return"}.
    """
    risk_free_rate = float(risk_free_rate)
    market_expected_return = float(market_expected_return)
    market_volatility = float(market_volatility)
    target_volatility = float(target_volatility)
    if market_volatility <= 0.0:
        raise ValueError("market_volatility must be positive")
    if target_volatility < 0.0:
        raise ValueError("target_volatility must be non-negative")

    sharpe = calculate_sharpe_ratio(market_expected_return, risk_free_rate, market_volatility)
    cml_return = capital_market_line(risk_free_rate, sharpe, target_volatility)
    return {
        "market_sharpe_ratio": float(sharpe),
        "cml_expected_return": float(cml_return),
    }


if __name__ == "__main__":
    # --- Example I.6.10 Implementation ---
    r_m = 0.10  # Market expected return = 10%
    sigma_m = 0.20  # Market standard deviation = 20%
    r_f = 0.05  # Risk-free rate = 5%

    # 1. Calculate the slope of the CML (Sharpe Ratio)
    market_sharpe = calculate_sharpe_ratio(r_m, r_f, sigma_m)

    # 2. Calculate the expected return for a portfolio with 15% volatility
    target_vol = 0.15
    portfolio_return = capital_market_line(r_f, market_sharpe, target_vol)

    print("--- Capital Market Line (CML) ---")
    print(f"CML Slope (Market Sharpe Ratio): {market_sharpe:.2f}")
    print(f"Expected Return for {target_vol * 100}% volatility: {portfolio_return * 100:.2f}%")
