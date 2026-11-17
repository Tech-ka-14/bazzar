"""Rolling-volatility 'ghost effect' demonstration.

Equally weighted T-day moving-average variance assigns weight 1/T to the
squared shock return for exactly T days after a single large return, so the
estimated volatility drops abruptly when the shock leaves the window — the
'ghost effect'.
"""

import numpy as np
import pandas as pd


def simulate_ghost_effect(T_window=30, total_days=100, shock_day=10, shock_magnitude=0.15):
    """
    Simulates a time series of returns to demonstrate the 'ghost effect'
    inherent in T-day equally weighted moving average volatility estimates.
    """
    # 1. Generate baseline zero-mean normal returns
    np.random.seed(42)
    returns = np.random.normal(0, 0.01, total_days)

    # 2. Inject a single massive market shock (e.g., 15% drop)
    returns[shock_day] = -shock_magnitude

    # 3. Calculate rolling T-day variance and volatility
    df = pd.DataFrame({"Returns": returns})
    df["Squared_Returns"] = df["Returns"] ** 2

    # The equally weighted variance is the rolling mean of squared returns
    df["Rolling_Variance"] = df["Squared_Returns"].rolling(window=T_window).mean()
    df["Rolling_Volatility"] = np.sqrt(df["Rolling_Variance"])

    # 4. Identify the ghost drop
    # The drop happens exactly T_window days after the shock_day
    ghost_day = shock_day + T_window

    return df, shock_day, ghost_day


def compute(
    T_window: int = 30, total_days: int = 100, shock_day: int = 10, shock_magnitude: float = 0.15
) -> dict:
    """Standard facade: ghost-effect simulation summary as a JSON dict.

    Parameters:
    T_window (int): Rolling window length of the equally weighted variance.
    total_days (int): Total number of simulated days (> T_window).
    shock_day (int): Day index on which the single shock return occurs.
    shock_magnitude (float): Size of the shock return (fraction, positive).

    Returns:
    dict: {"t_window", "shock_day", "ghost_day", "peak_rolling_volatility",
    "rolling_volatility_after_ghost"} with plain floats/ints. The peak is
    reached while the shock sits inside the window; the value after the
    ghost day shows the abrupt drop once it leaves the window.
    """
    T_window = int(T_window)
    total_days = int(total_days)
    shock_day = int(shock_day)
    if T_window < 1:
        raise ValueError("T_window must be at least 1")
    if total_days <= T_window:
        raise ValueError("total_days must exceed T_window")
    if not 0 <= shock_day < total_days - T_window:
        raise ValueError("shock_day must leave a full window of days after it")

    df, shock_idx, ghost_idx = simulate_ghost_effect(
        T_window=T_window,
        total_days=total_days,
        shock_day=shock_day,
        shock_magnitude=float(shock_magnitude),
    )
    rolling_vol = df["Rolling_Volatility"].dropna()
    return {
        "t_window": T_window,
        "shock_day": int(shock_idx),
        "ghost_day": int(ghost_idx),
        "peak_rolling_volatility": float(rolling_vol.max()),
        "rolling_volatility_after_ghost": float(df["Rolling_Volatility"].iloc[-1]),
    }


if __name__ == "__main__":
    # Generate the simulation
    sim_data, shock_idx, ghost_idx = simulate_ghost_effect(T_window=30)
