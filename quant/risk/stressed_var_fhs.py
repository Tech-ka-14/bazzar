"""Stressed VaR via filtered historical simulation (FHS).

Bootstraps empirical standardized residuals through an asymmetric GARCH
variance recursion starting from a shock state, for a gradually
liquidated portfolio, to produce stressed simulated total returns.
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.3.5
(filtered historical simulation).
"""

import numpy as np


def simulate_stressed_fhs_garch(
    historical_standardized_residuals: np.ndarray,
    n_simulations: int,
    h_days: int,
    shock_return: float,
    shock_vol_annual: float,
    omega: float,
    alpha: float,
    beta: float,
    lambda_asym: float,
) -> np.ndarray:
    """
    Simulates total returns for a gradually liquidated portfolio under stressed conditions
    using Filtered Historical Simulation (bootstrapping empirical residuals).
    """
    shock_var_daily = (shock_vol_annual / np.sqrt(250)) ** 2
    liquidation_weights = np.array([(h_days - t + 1) / h_days for t in range(1, h_days + 1)])

    total_simulated_returns = np.zeros(n_simulations)
    n_historical_obs = len(historical_standardized_residuals)

    for i in range(n_simulations):
        current_var = shock_var_daily
        prev_return = shock_return
        path_returns = np.zeros(h_days)

        # Bootstrap: Draw h random indices with replacement from historical data
        random_indices = np.random.randint(0, n_historical_obs, h_days)
        z_shocks = historical_standardized_residuals[random_indices]

        for t in range(h_days):
            current_var = omega + alpha * (prev_return - lambda_asym) ** 2 + beta * current_var
            current_vol = np.sqrt(current_var)

            # Generate today's simulated return using the empirical standardized residual
            current_return = current_vol * z_shocks[t]
            path_returns[t] = current_return
            prev_return = current_return

        total_simulated_returns[i] = np.sum(path_returns * liquidation_weights)

    return total_simulated_returns


def compute(
    historical_standardized_residuals,
    n_simulations: int = 10000,
    h_days: int = 10,
    shock_return: float = -0.05,
    shock_vol_annual: float = 0.40,
    omega: float = 1e-6,
    alpha_garch: float = 0.05,
    beta: float = 0.90,
    lambda_asym: float = 0.0,
    alpha: float = 0.01,
    seed: int = None,
) -> dict:
    """Standard facade: stressed FHS VaR/ETL as a JSON-serializable dict.

    Parameters:
    historical_standardized_residuals: 1-D array-like of standardized
    residuals to bootstrap.
    n_simulations (int): Number of Monte Carlo paths.
    h_days (int): Liquidation horizon in days.
    shock_return (float): Initial (day-0) stressed return.
    shock_vol_annual (float): Annualized shock volatility (positive).
    omega, alpha_garch, beta (float): GARCH variance recursion parameters.
    lambda_asym (float): Asymmetry (leverage) shift parameter.
    alpha (float): Tail probability in (0, 1), e.g. 0.01.
    seed (int, optional): RNG seed for reproducibility.

    Returns:
    dict: {"method", "alpha", "h_days", "n_simulations", "var", "etl"}
    with positive loss fractions.
    """
    residuals = np.asarray(historical_standardized_residuals, dtype=float).ravel()
    if residuals.size == 0:
        raise ValueError("historical_standardized_residuals must be non-empty")
    if shock_vol_annual <= 0:
        raise ValueError("shock_vol_annual must be positive")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")
    if seed is not None:
        np.random.seed(seed)

    sims = simulate_stressed_fhs_garch(
        residuals,
        int(n_simulations),
        int(h_days),
        float(shock_return),
        float(shock_vol_annual),
        float(omega),
        float(alpha_garch),
        float(beta),
        float(lambda_asym),
    )
    var = float(-np.quantile(sims, alpha))
    tail = sims[sims < -var]
    etl = float(-np.mean(tail)) if tail.size > 0 else var
    return {
        "method": "stressed_fhs",
        "alpha": float(alpha),
        "h_days": int(h_days),
        "n_simulations": int(n_simulations),
        "var": var,
        "etl": etl,
    }
