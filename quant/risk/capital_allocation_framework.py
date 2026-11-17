"""Regulatory market capital and economic capital allocation.

Regulatory capital follows the Basel internal-model 1% 10-day VaR;
economic capital allows flexible horizons/confidence and Expected Tail
Loss (ETL) instead of VaR.
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.6.
"""

import numpy as np


def calculate_regulatory_market_capital(
    simulated_daily_returns: np.ndarray, portfolio_value: float
) -> float:
    """
    Calculates the minimum Regulatory Capital using the Basel Internal Model approach.
    Strictly requires a 1% confidence level over a 10-day horizon.
    """
    # Regulatory parameters
    alpha = 0.01
    h_days = 10

    # Scale daily simulated returns to h-day returns (Assuming i.i.d for this basic example)
    # In practice, multi-step simulation (as built previously) is preferred.
    h_day_returns = simulated_daily_returns * np.sqrt(h_days)

    # Calculate 1% VaR as a percentage
    var_percent = -np.quantile(h_day_returns, alpha)

    # Capital required is the Value at Risk in absolute terms
    regulatory_capital = var_percent * portfolio_value
    return regulatory_capital


def calculate_economic_capital(
    simulated_horizon_returns: np.ndarray,
    portfolio_value: float,
    alpha: float,
    use_etl: bool = True,
) -> float:
    """
    Calculates the internal Economic Capital for solvency and credit-rating purposes.
    Allows for flexible horizons, confidence levels, and the use of Expected Tail Loss (ETL).
    """
    var_percent = -np.quantile(simulated_horizon_returns, alpha)

    if use_etl:
        # Calculate Expected Tail Loss (Average of losses exceeding VaR)
        tail_losses = simulated_horizon_returns[simulated_horizon_returns < -var_percent]
        etl_percent = -np.mean(tail_losses) if len(tail_losses) > 0 else var_percent
        economic_capital = etl_percent * portfolio_value
    else:
        economic_capital = var_percent * portfolio_value

    return economic_capital


# Example Usage:
# Assume we have 10,000 simulated daily returns for a $100M portfolio


def compute(
    returns, portfolio_value: float = 1.0, alpha: float = 0.01, use_etl: bool = True
) -> dict:
    """Standard facade: economic capital from simulated horizon returns.

    Parameters:
    returns: 1-D array-like of simulated h-day returns (fractions).
    portfolio_value (float): Nominal portfolio value.
    alpha (float): Tail probability in (0, 1), e.g. 0.01.
    use_etl (bool): Base capital on ETL (True) or VaR (False).

    Returns:
    dict: {"method", "alpha", "n", "portfolio_value", "capital",
    "capital_pct"}.
    """
    returns = np.asarray(returns, dtype=float).ravel()
    if returns.size == 0:
        raise ValueError("returns must contain at least one observation")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    capital = calculate_economic_capital(
        returns, float(portfolio_value), float(alpha), use_etl=bool(use_etl)
    )
    return {
        "method": "economic_capital_etl" if use_etl else "economic_capital_var",
        "alpha": float(alpha),
        "n": int(returns.size),
        "portfolio_value": float(portfolio_value),
        "capital": float(capital),
        "capital_pct": float(capital / portfolio_value),
    }


if __name__ == "__main__":
    simulated_returns = np.random.normal(0.0005, 0.015, 10000)
    portfolio_value = 100_000_000

    # 1. Bank computes regulatory requirement (Strict 1% 10-Day VaR)
    reg_capital = calculate_regulatory_market_capital(simulated_returns, portfolio_value)

    # 2. Bank computes its own internal Economic Capital using a stricter 0.1% ETL over 1-year (250 days)
    # (Simulating an annualized horizon based on daily data for demonstration)
    annualized_returns = simulated_returns * np.sqrt(250)
    econ_capital = calculate_economic_capital(
        annualized_returns, portfolio_value, alpha=0.001, use_etl=True
    )
