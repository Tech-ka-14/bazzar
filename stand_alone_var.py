import numpy as np
from scipy.stats import norm

def calculate_standalone_var(theta_isolated: np.ndarray, omega_isolated: np.ndarray, alpha: float = 0.01) -> float:
    """
    Calculates the Stand-Alone VaR for a specific partition (e.g., Equity only).
    Equations IV.2.19, IV.2.20, IV.2.21.
    """
    variance = theta_isolated.T @ omega_isolated @ theta_isolated
    critical_value = norm.ppf(1 - alpha)
    return critical_value * np.sqrt(variance)

# Example: Disaggregating a 3-factor portfolio (1 Equity, 1 FX, 1 IR)
theta_full = np.array([100000, 50000, 25000]) # Nominal Sensitivities
omega_full = np.array([
    [0.04,  0.01, -0.005], # Eq
    [0.01,  0.02,  0.002], # FX
    [-0.005, 0.002, 0.01]  # IR
])

# Isolate partitions
eq_var = calculate_standalone_var(theta_full[0:1], omega_full[0:1, 0:1])
fx_var = calculate_standalone_var(theta_full[1:2], omega_full[1:2, 1:2])
ir_var = calculate_standalone_var(theta_full[2:3], omega_full[2:3, 2:3])

# Calculate Total Systematic VaR
total_var = calculate_standalone_var(theta_full, omega_full)

print(f"Stand-Alone Equity VaR: ${eq_var:,.2f}")
print(f"Stand-Alone FX VaR: ${fx_var:,.2f}")
print(f"Stand-Alone IR VaR: ${ir_var:,.2f}")
print("-" * 30)
print(f"Sum of Stand-Alone VaRs: ${eq_var + fx_var + ir_var:,.2f}")
print(f"Total Systematic VaR (Diversified): ${total_var:,.2f}")