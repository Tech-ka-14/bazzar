"""EWMA specific VaR from a dynamic factor model.

EWMA estimates of the factor variance and covariance give a dynamic
beta; the EWMA volatility of the residuals drives the specific
(idiosyncratic) VaR of the portfolio.
Reference: Alexander (2008), Market Risk Analysis IV, Equation IV.2.48.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm


def calculate_ewma_specific_var(
    portfolio_returns: pd.Series,
    factor_returns: pd.Series,
    lam: float = 0.95,
    alpha: float = 0.01,
    h_days: int = 10,
):
    """
    Calculates the highly risk-sensitive Specific VaR using EWMA for beta
    and residual variance (Equation IV.2.48).
    """
    # 1. Calculate EWMA Variance of the Factor and EWMA Covariance
    ewma_var_x = factor_returns.ewm(alpha=1 - lam, adjust=False).var()
    ewma_cov_xy = factor_returns.ewm(alpha=1 - lam, adjust=False).cov(portfolio_returns)

    # 2. Calculate dynamic EWMA Beta
    ewma_beta = ewma_cov_xy / ewma_var_x

    # 3. Calculate dynamic residuals: e_t = Y_t - (beta_t * X_t)
    residuals = portfolio_returns - (ewma_beta * factor_returns)

    # 4. Calculate EWMA Volatility of the residuals (sigma^e_t)
    ewma_residual_vol = np.sqrt(residuals.ewm(alpha=1 - lam, adjust=False).var())

    # 5. Calculate Specific VaR for the most recent observation
    latest_residual_vol = ewma_residual_vol.iloc[-1]
    critical_val = norm.ppf(1 - alpha)

    specific_var_h = critical_val * np.sqrt(h_days) * latest_residual_vol

    return specific_var_h, ewma_beta.iloc[-1]


# Simulated market data (100 days)


def compute(
    portfolio_returns, factor_returns, lam: float = 0.95, alpha: float = 0.01, h_days: int = 10
) -> dict:
    """Standard facade: EWMA specific VaR as a JSON-serializable dict.

    Parameters:
    portfolio_returns: 1-D array-like of portfolio returns.
    factor_returns: 1-D array-like of factor (market) returns, same length.
    lam (float): EWMA smoothing constant in (0, 1).
    alpha (float): Tail probability in (0, 1), e.g. 0.01.
    h_days (int): Risk horizon in days.

    Returns:
    dict: {"method", "alpha", "h_days", "n", "specific_var", "beta"}.
    """
    portfolio_returns = pd.Series(np.asarray(portfolio_returns, dtype=float).ravel())
    factor_returns = pd.Series(np.asarray(factor_returns, dtype=float).ravel())
    if portfolio_returns.size < 2:
        raise ValueError("portfolio_returns must contain at least two observations")
    if factor_returns.size != portfolio_returns.size:
        raise ValueError("factor_returns must have the same length as portfolio_returns")
    if not 0.0 < lam < 1.0:
        raise ValueError("lam must be in the open interval (0, 1)")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    spec_var, beta = calculate_ewma_specific_var(
        portfolio_returns, factor_returns, float(lam), float(alpha), int(h_days)
    )
    return {
        "method": "ewma_specific",
        "alpha": float(alpha),
        "h_days": int(h_days),
        "n": int(portfolio_returns.size),
        "specific_var": float(spec_var),
        "beta": float(beta),
    }


if __name__ == "__main__":
    np.random.seed(42)
    market_returns = pd.Series(np.random.normal(0, 0.01, 100))
    # Portfolio has beta of ~1.2 plus some idiosyncratic noise
    port_returns = pd.Series(1.2 * market_returns + np.random.normal(0, 0.005, 100))

    # Execute EWMA Specific VaR calculation
    spec_var, current_beta = calculate_ewma_specific_var(
        port_returns, market_returns, lam=0.95, alpha=0.01, h_days=10
    )

    print(f"Current EWMA Beta Estimate: {current_beta:.4f}")
    print(f"1% 10-day EWMA Specific VaR (Percentage): {spec_var:.4%}")
