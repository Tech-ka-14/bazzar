"""Stand-alone VaR of a yield-curve partition.

Isolates a sub-block of risk factors (e.g. one country's curve or credit
spreads) from the full sensitivity vector and covariance matrix and
computes the stand-alone normal linear VaR of that partition.
Reference: Alexander (2008), Market Risk Analysis IV, Example IV.2.5.
"""

import numpy as np
from scipy.stats import norm


def calculate_partitioned_var(
    theta_full: np.ndarray, omega_full: np.ndarray, slice_indices: list, alpha: float = 0.01
) -> float:
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


def compute(theta_full, omega_full, slice_indices, alpha: float = 0.01) -> dict:
    """Standard facade: partitioned stand-alone VaR as a JSON dict.

    Parameters:
    theta_full: 1-D array-like of the full sensitivity vector.
    omega_full: Square covariance matrix matching len(theta_full).
    slice_indices: Indices of the sub-block to isolate (non-empty).
    alpha (float): Tail probability in (0, 1), e.g. 0.01.

    Returns:
    dict: {"method", "alpha", "n_partition", "var"} with "var" the
    positive loss.
    """
    theta = np.asarray(theta_full, dtype=float).ravel()
    omega = np.asarray(omega_full, dtype=float)
    idx = [int(i) for i in slice_indices]
    if theta.size == 0:
        raise ValueError("theta_full must contain at least one sensitivity")
    if omega.shape != (theta.size, theta.size):
        raise ValueError("omega_full must be square with size len(theta_full)")
    if not idx or min(idx) < 0 or max(idx) >= theta.size:
        raise ValueError("slice_indices must be valid indices into theta_full")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    var = calculate_partitioned_var(theta, omega, idx, float(alpha))
    return {
        "method": "partitioned_var",
        "alpha": float(alpha),
        "n_partition": int(len(idx)),
        "var": float(var),
    }


if __name__ == "__main__":
    theta_total = np.array([1000, -1500, 2000, 800, 900, -750])

    # (Abbreviated dummy matrix for structural demonstration)
    omega_total = np.eye(6) * 10000
    us_indices = [0, 1, 2]
    uk_indices = [3, 4, 5]

    us_standalone_var = calculate_partitioned_var(theta_total, omega_total, us_indices)
    uk_standalone_var = calculate_partitioned_var(theta_total, omega_total, uk_indices)

    print(f"US Stand-Alone Interest Rate VaR: ${us_standalone_var:,.2f}")
    print(f"UK Stand-Alone Interest Rate VaR: ${uk_standalone_var:,.2f}")
