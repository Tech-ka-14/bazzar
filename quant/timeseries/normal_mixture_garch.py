"""Normal-mixture GARCH VaR.

Simulates GARCH paths separately under two normal volatility regimes and
mixes them with the regime probability, capturing time-varying volatility
and heavy tails for VaR estimation.
"""

import numpy as np


def simulate_normal_mixture_garch(
    n_simulations: int,
    h_days: int,
    prob_crash: float,
    garch_params_crash: dict,
    garch_params_normal: dict,
) -> np.ndarray:
    """
    Simulates returns using a Normal Mixture GARCH model (two volatility regimes).
    """
    # Determine how many simulations fall into each regime
    n_crash = int(n_simulations * prob_crash)
    n_normal = n_simulations - n_crash

    # Inner function to run a standard GARCH(1,1) simulation
    def run_garch(n, omega, alpha, beta):
        sims = np.zeros((n, h_days))
        # Start at stationary variance
        current_var = np.full(n, omega / (1 - alpha - beta))

        for t in range(h_days):
            z = np.random.standard_normal(n)
            current_vol = np.sqrt(current_var)
            r_t = current_vol * z
            sims[:, t] = r_t
            # Update variance
            current_var = omega + (alpha * r_t**2) + (beta * current_var)
        return np.sum(sims, axis=1)  # Return total h-day return

    # Run simulations for both regimes
    crash_sims = run_garch(n_crash, **garch_params_crash)
    normal_sims = run_garch(n_normal, **garch_params_normal)

    # Combine into a single mixed distribution
    combined_sims = np.concatenate((crash_sims, normal_sims))
    np.random.shuffle(combined_sims)

    return combined_sims


def compute(
    prob_crash: float,
    garch_params_crash,
    garch_params_normal,
    h_days: int = 10,
    n_simulations: int = 10000,
    alpha: float = 0.01,
) -> dict:
    """Standard facade: normal-mixture GARCH VaR/ETL as a JSON dict.

    Parameters:
    prob_crash (float): Probability of the crash regime in (0, 1).
    garch_params_crash (dict): {"omega", "alpha", "beta"} of the crash
    regime (positive omega, non-negative alpha/beta with alpha+beta < 1).
    garch_params_normal (dict): Same for the normal regime.
    h_days (int): Risk horizon in days (>= 1).
    n_simulations (int): Total number of simulated paths (>= 2).
    alpha (float): Tail probability in (0, 1), e.g. 0.01.

    Returns:
    dict: {"alpha", "h_days", "n_simulations", "prob_crash", "var",
    "etl"} with positive loss fractions.
    """
    prob_crash = float(prob_crash)
    if not 0.0 < prob_crash < 1.0:
        raise ValueError("prob_crash must be in the open interval (0, 1)")
    h_days = int(h_days)
    n_simulations = int(n_simulations)
    if h_days < 1 or n_simulations < 2:
        raise ValueError("h_days >= 1 and n_simulations >= 2 are required")
    if not 0.0 < float(alpha) < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    for params, name in ((garch_params_crash, "crash"), (garch_params_normal, "normal")):
        if not isinstance(params, dict) or not {"omega", "alpha", "beta"} <= set(params):
            raise ValueError(f"garch_params_{name} must define omega, alpha and beta")
        omega, arch, garch = float(params["omega"]), float(params["alpha"]), float(params["beta"])
        if omega <= 0.0 or arch < 0.0 or garch < 0.0 or arch + garch >= 1.0:
            raise ValueError(
                f"garch_params_{name} must have omega > 0, alpha/beta >= 0, alpha+beta < 1"
            )

    sims = simulate_normal_mixture_garch(
        n_simulations,
        h_days,
        prob_crash,
        {k: float(v) for k, v in garch_params_crash.items()},
        {k: float(v) for k, v in garch_params_normal.items()},
    )
    var = float(-np.quantile(sims, float(alpha)))
    tail = sims[sims < -var]
    etl = float(-np.mean(tail)) if tail.size > 0 else var
    return {
        "alpha": float(alpha),
        "h_days": h_days,
        "n_simulations": n_simulations,
        "prob_crash": prob_crash,
        "var": var,
        "etl": etl,
    }


if __name__ == "__main__":
    # Example Parameters
    crash_params = {"omega": 0.0005, "alpha": 0.15, "beta": 0.80}  # High persistence, high vol
    normal_params = {"omega": 0.0001, "alpha": 0.05, "beta": 0.90}  # Low vol regime
    crash_prob = 0.05  # 5% chance of being in a crash regime

    mixed_returns = simulate_normal_mixture_garch(
        10000, 10, crash_prob, crash_params, normal_params
    )

    var_99 = -np.quantile(mixed_returns, 0.01)
    print(f"1% 10-Day Normal Mixture GARCH VaR: {var_99:.4f}")
