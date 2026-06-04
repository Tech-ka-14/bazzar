import numpy as np
from scipy.stats import norm

def calculate_partitioned_var(theta_full: np.ndarray, omega_full: np.ndarray, slice_indices: list, alpha: float = 0.01) -> float:
    """
    Isolates a sub-matrix of risk factors (e.g., only the UK curve or only Credit Spreads)
    and calculates the Stand-Alone VaR for that partition.
    """
    # Extract the isolated sensitivities
    theta_isolated = theta_full[slice_indices]
    
    # Extract the isolated covariance sub-matrix using np.ix_
    omega_isolated = omega_full[np.ix_(slice_indices, slice_indices)]
    
    # Calculate Stand-Alone VaR
    variance = theta_isolated.T @ omega_isolated @ theta_isolated
    return norm.ppf(1 - alpha) * np.sqrt(variance)

# Structure of Example IV.2.5: US (indices 0,1,2) and UK (indices 3,4,5)
theta_total = np.array([1000, -1500, 2000, 800, 900, -750])

# (Abbreviated dummy matrix for structural demonstration)
omega_total = np.eye(6) * 10000 
us_indices = [0, 1, 2]
uk_indices = [3, 4, 5]

us_standalone_var = calculate_partitioned_var(theta_total, omega_total, us_indices)
uk_standalone_var = calculate_partitioned_var(theta_total, omega_total, uk_indices)

print(f"US Stand-Alone Interest Rate VaR: ${us_standalone_var:,.2f}")
print(f"UK Stand-Alone Interest Rate VaR: ${uk_standalone_var:,.2f}")