"""Total systematic, equity and FX VaR of a foreign (quanto) position.

Decomposes the systematic VaR of a foreign equity position into
stand-alone equity and FX components including the quanto correlation.
Reference: Alexander (2008), Market Risk Analysis IV, Equations
IV.2.49-IV.2.52, Example IV.2.14.
"""

import numpy as np
from scipy.stats import norm


def calculate_quanto_var_components(
    equity_beta: float,
    vol_equity: float,
    vol_fx: float,
    quanto_corr: float,
    portfolio_val: float,
    horizon_days: int = 10,
    alpha: float = 0.01,
):
    """
    Calculates the Total Systematic, Stand-alone Equity, and Stand-alone FX VaR
    incorporating the quanto correlation (Equations IV.2.49 to IV.2.52).
    """
    # Scale annual volatilities to the specific horizon
    time_scale = np.sqrt(horizon_days / 250.0)
    vol_eq_h = vol_equity * time_scale
    vol_fx_h = vol_fx * time_scale

    # Calculate Total Portfolio Volatility (Eq IV.2.49)
    variance_h = (
        (equity_beta**2 * vol_eq_h**2)
        + (vol_fx_h**2)
        + (2 * equity_beta * quanto_corr * vol_eq_h * vol_fx_h)
    )
    vol_total_h = np.sqrt(variance_h)

    # Calculate VaRs
    z_score = norm.ppf(1 - alpha)

    total_var = z_score * vol_total_h * portfolio_val
    equity_var = z_score * (equity_beta * vol_eq_h) * portfolio_val
    fx_var = z_score * vol_fx_h * portfolio_val

    return total_var, equity_var, fx_var


# Example IV.2.14: Equity and Forex VaR


def compute(
    equity_beta: float,
    vol_equity: float,
    vol_fx: float,
    quanto_corr: float,
    portfolio_value: float = 1.0,
    horizon_days: int = 10,
    alpha: float = 0.01,
) -> dict:
    """Standard facade: quanto equity/FX VaR decomposition as a JSON dict.

    Parameters:
    equity_beta (float): Beta of the foreign position to its equity index.
    vol_equity, vol_fx (float): Annual volatilities (positive).
    quanto_corr (float): Correlation between equity and FX returns.
    portfolio_value (float): Nominal position value.
    horizon_days (int): Risk horizon in days.
    alpha (float): Tail probability in (0, 1), e.g. 0.01.

    Returns:
    dict: {"method", "alpha", "horizon_days", "var_total", "var_equity",
    "var_fx"} with positive monetary losses.
    """
    if vol_equity <= 0 or vol_fx <= 0:
        raise ValueError("vol_equity and vol_fx must be positive")
    if not -1.0 <= quanto_corr <= 1.0:
        raise ValueError("quanto_corr must be in [-1, 1]")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    total, eq_var, fx_var = calculate_quanto_var_components(
        float(equity_beta),
        float(vol_equity),
        float(vol_fx),
        float(quanto_corr),
        float(portfolio_value),
        int(horizon_days),
        float(alpha),
    )
    return {
        "method": "quanto",
        "alpha": float(alpha),
        "horizon_days": int(horizon_days),
        "var_total": float(total),
        "var_equity": float(eq_var),
        "var_fx": float(fx_var),
    }


if __name__ == "__main__":
    portfolio_usd = 2_000_000
    beta_uk = 1.5
    vol_ftse = 0.15
    vol_gbpusd = 0.20
    correlation = 0.30

    total, eq_var, fx_var = calculate_quanto_var_components(
        beta_uk, vol_ftse, vol_gbpusd, correlation, portfolio_usd, horizon_days=10
    )

    print(f"Stand-alone Equity VaR: ${eq_var:,.0f}")
    print(f"Stand-alone Forex VaR: ${fx_var:,.0f}")
    print(f"Sum of Stand-alone VaRs: ${eq_var + fx_var:,.0f}")
    print("-" * 35)
    print(f"Total Systematic VaR (Diversified): ${total:,.0f}")
