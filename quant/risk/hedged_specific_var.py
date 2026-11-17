"""Specific VaR of a fully hedged portfolio (tracking-error risk).

After hedging systematic market risk, the remaining specific variance is
sigma_p^2 - beta^2 sigma_m^2; specific VaR is the normal quantile times
the horizon-scaled specific volatility and portfolio value.
Reference: Alexander (2008), Market Risk Analysis IV, Example IV.2.17(c).
"""

import numpy as np
from scipy.stats import norm


def calculate_hedged_specific_var(
    portfolio_vol_annual: float,
    market_vol_annual: float,
    portfolio_beta: float,
    portfolio_value: float,
    horizon_days: int = 1,
    alpha: float = 0.01,
):
    """
    Calculates the 1-day Specific VaR (Tracking Error risk) remaining
    after completely hedging systematic market risk.
    """
    # 1. Calculate specific variance (annualized)
    specific_variance_annual = (portfolio_vol_annual**2) - (
        portfolio_beta**2 * market_vol_annual**2
    )

    if specific_variance_annual < 0:
        raise ValueError("Invalid parameters: Systematic variance exceeds total variance.")

    # 2. Scale specific variance to target horizon
    specific_variance_h = specific_variance_annual * (horizon_days / 250.0)
    specific_volatility_h = np.sqrt(specific_variance_h)

    # 3. Calculate Specific VaR
    z_score = norm.ppf(1 - alpha)
    specific_var = z_score * specific_volatility_h * portfolio_value

    return specific_var


# Example IV.2.17(c): Specific VaR of Hedged European S&P500 Portfolio


def compute(
    portfolio_vol_annual: float,
    market_vol_annual: float,
    portfolio_beta: float,
    portfolio_value: float = 1.0,
    horizon_days: int = 1,
    alpha: float = 0.01,
) -> dict:
    """Standard facade: hedged specific VaR as a JSON-serializable dict.

    Parameters:
    portfolio_vol_annual, market_vol_annual (float): Annual volatilities.
    portfolio_beta (float): Portfolio beta to the market factor.
    portfolio_value (float): Nominal portfolio value.
    horizon_days (int): Risk horizon in days.
    alpha (float): Tail probability in (0, 1), e.g. 0.01.

    Returns:
    dict: {"method", "alpha", "horizon_days", "specific_var"}.
    """
    if portfolio_vol_annual <= 0 or market_vol_annual <= 0:
        raise ValueError("volatilities must be positive")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    spec_var = calculate_hedged_specific_var(
        float(portfolio_vol_annual),
        float(market_vol_annual),
        float(portfolio_beta),
        float(portfolio_value),
        int(horizon_days),
        float(alpha),
    )
    return {
        "method": "hedged_specific",
        "alpha": float(alpha),
        "horizon_days": int(horizon_days),
        "specific_var": float(spec_var),
    }


if __name__ == "__main__":
    port_value = 5_000_000
    port_vol = 0.35
    market_beta = 1.50
    market_vol = 0.20

    spec_var = calculate_hedged_specific_var(
        portfolio_vol_annual=port_vol,
        market_vol_annual=market_vol,
        portfolio_beta=market_beta,
        portfolio_value=port_value,
        horizon_days=1,
    )

    print(f"Portfolio Value: ${port_value:,.0f}")
    print(f"1% 1-Day Specific VaR (Tracking Risk): ${spec_var:,.0f}")
