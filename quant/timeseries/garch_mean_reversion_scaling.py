"""GARCH(1,1) mean-reversion scaling for VaR horizons.

Daily returns are simulated from a GARCH(1,1) process and aggregated over
h days; the scaling factor sigma_h / (sqrt(h) * sigma_1) shows how the
empirical VaR horizon scaling decays toward the square-root-of-time rule as
volatility mean-reverts.
"""

import numpy as np


def simulate_garch_var_scaling(
    n_simulations: int, h_days: int, omega: float, alpha: float, beta: float
) -> tuple:
    """
    Simulates 1-day and h-day returns using a GARCH(1,1) process to demonstrate
    how volatility mean reversion alters the scaling of VaR.
    """
    # Stationary variance (long-run average volatility)
    stationary_variance = omega / (1 - alpha - beta)

    returns_1d = np.zeros(n_simulations)
    returns_hd = np.zeros(n_simulations)

    for i in range(n_simulations):
        # Start each simulation at the stationary variance
        current_variance = stationary_variance
        total_return = 0.0

        for t in range(h_days):
            # 1. Calculate current volatility
            current_vol = np.sqrt(current_variance)

            # 2. Generate the return for today
            z = np.random.standard_normal()
            r_t = current_vol * z

            # 3. Accumulate for the h-day return
            total_return += r_t

            # 4. Update GARCH variance for tomorrow based on today's shock
            current_variance = omega + alpha * (r_t**2) + beta * current_variance

            # Save the 1-day return separately
            if t == 0:
                returns_1d[i] = r_t

        returns_hd[i] = total_return

    # Calculate the empirical volatilities of the simulated distributions
    vol_1d = np.std(returns_1d)
    vol_hd = np.std(returns_hd)

    # The scaling factor tells us how much the true h-day vol deviates from sqrt(h) rule
    scaling_factor = vol_hd / (np.sqrt(h_days) * vol_1d)

    return vol_1d, vol_hd, scaling_factor


def compute(
    omega: float, alpha: float, beta: float, h_days: int = 10, n_simulations: int = 10000
) -> dict:
    """Standard facade: GARCH scaling-factor simulation as a JSON dict.

    Parameters:
    omega (float): GARCH constant variance term, must be positive.
    alpha (float): ARCH coefficient (>= 0).
    beta (float): GARCH coefficient (>= 0); alpha + beta must be < 1 for a
    stationary process.
    h_days (int): Aggregation horizon in days (>= 1).
    n_simulations (int): Number of simulated paths (>= 2).

    Returns:
    dict: {"h_days", "n_simulations", "stationary_daily_vol", "vol_1d",
    "vol_hd", "scaling_factor"} with plain floats/ints. A scaling factor
    below 1 means risk scales slower than the square root of time.
    """
    omega = float(omega)
    alpha = float(alpha)
    beta = float(beta)
    h_days = int(h_days)
    n_simulations = int(n_simulations)
    if omega <= 0.0:
        raise ValueError("omega must be positive")
    if alpha < 0.0 or beta < 0.0:
        raise ValueError("alpha and beta must be non-negative")
    if alpha + beta >= 1.0:
        raise ValueError("alpha + beta must be < 1 for a stationary GARCH process")
    if h_days < 1:
        raise ValueError("h_days must be at least 1")
    if n_simulations < 2:
        raise ValueError("n_simulations must be at least 2")

    vol_1d, vol_hd, scaling_factor = simulate_garch_var_scaling(
        n_simulations, h_days, omega, alpha, beta
    )
    return {
        "h_days": h_days,
        "n_simulations": n_simulations,
        "stationary_daily_vol": float(np.sqrt(omega / (1 - alpha - beta))),
        "vol_1d": float(vol_1d),
        "vol_hd": float(vol_hd),
        "scaling_factor": float(scaling_factor),
    }


if __name__ == "__main__":
    # Example Parameters (High persistence alpha+beta = 0.95, typical for financial returns)
    garch_omega = 0.0001
    garch_alpha = 0.10
    garch_beta = 0.85
    horizon = 10

    vol_1, vol_h, factor = simulate_garch_var_scaling(
        10000, horizon, garch_omega, garch_alpha, garch_beta
    )

    print(f"Stationary Daily Vol: {np.sqrt(garch_omega / (1 - garch_alpha - garch_beta)):.4f}")
    print(f"Empirical 1-Day Vol: {vol_1:.4f}")
    print(f"Empirical {horizon}-Day Vol: {vol_h:.4f}")
    print(f"Scaling Factor: {factor:.4f}")
    print(
        f"(If the scaling factor is < 1.0, GARCH mean reversion causes risk to scale slower than the square root of time)"
    )
