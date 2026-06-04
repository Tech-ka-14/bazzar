import numpy as np

def calculate_adjusted_time_horizon(h: int, rho: float) -> float:
    """Calculates adjusted time horizon (h_tilde) for AR1 process."""
    if rho == 0:
        return float(h)
    term_1 = (h - 1) * (1 - rho)
    term_2 = rho * (1 - rho**(h - 1))
    return h + 2 * (rho / (1 - rho)**2) * (term_1 - term_2)

# Example IV.2.23: Mixture VaR with Autocorrelation
h_days = 10
rho_positive = 0.25
rho_negative = -0.25

h_tilde_pos = calculate_adjusted_time_horizon(h_days, rho_positive)
h_tilde_neg = calculate_adjusted_time_horizon(h_days, rho_negative)

print(f"Standard Time Horizon (h): {h_days}")
print(f"Adjusted Horizon (Autocorrelation = +0.25): {h_tilde_pos:.2f}")
print(f"Adjusted Horizon (Autocorrelation = -0.25): {h_tilde_neg:.2f}\n")

print(f"If calculating 10-day Mixture VaR with +0.25 autocorrelation, scale daily volatilities by sqrt({h_tilde_pos:.2f}) (approx {np.sqrt(h_tilde_pos):.2f}) instead of sqrt({h_days}).")