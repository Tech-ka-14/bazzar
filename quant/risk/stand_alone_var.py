"""Stand-alone VaR of a portfolio partition under the normal linear model.

Stand-alone VaR of a position/sensitivity vector theta with covariance
matrix Omega at tail probability alpha is z_{1-alpha} * sqrt(theta' Omega
theta) (Equations IV.2.19-IV.2.21, Alexander 2008). The undiversified VaR is
the sum of the stand-alone VaRs; the diversified VaR uses the full matrix.
"""

import numpy as np
from scipy.stats import norm


def calculate_standalone_var(
    theta_isolated: np.ndarray, omega_isolated: np.ndarray, alpha: float = 0.01
) -> float:
    """
    Calculates the Stand-Alone VaR for a specific partition (e.g., Equity only).
    Equations IV.2.19, IV.2.20, IV.2.21.
    """
    variance = theta_isolated.T @ omega_isolated @ theta_isolated
    critical_value = norm.ppf(1 - alpha)
    return critical_value * np.sqrt(variance)


def compute(positions, cov_matrix, confidence: float = 0.99) -> dict:
    """Standard facade: diversified, stand-alone and undiversified VaR.

    Parameters:
    positions: 1-D array-like of nominal positions/sensitivities per asset.
    cov_matrix: 2-D covariance matrix of the risk factors (array-like).
    confidence (float): Confidence level in (0, 1), e.g. 0.99.

    Returns:
    dict: {"confidence", "total_var", "standalone_vars", "undiversified_var"}
    where total_var is the diversified VaR of the full portfolio and
    undiversified_var the sum of the per-asset stand-alone VaRs.
    """
    positions = np.asarray(positions, dtype=float).ravel()
    cov_matrix = np.asarray(cov_matrix, dtype=float)
    if cov_matrix.shape != (positions.size, positions.size):
        raise ValueError("cov_matrix must be square with side len(positions)")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in the open interval (0, 1)")

    alpha = 1.0 - float(confidence)
    total_var = float(calculate_standalone_var(positions, cov_matrix, alpha))
    standalone_vars = [
        float(
            calculate_standalone_var(positions[i : i + 1], cov_matrix[i : i + 1, i : i + 1], alpha)
        )
        for i in range(positions.size)
    ]
    return {
        "confidence": float(confidence),
        "total_var": total_var,
        "standalone_vars": standalone_vars,
        "undiversified_var": float(np.sum(standalone_vars)),
    }


if __name__ == "__main__":
    # Example: Disaggregating a 3-factor portfolio (1 Equity, 1 FX, 1 IR)
    theta_full = np.array([100000, 50000, 25000])  # Nominal Sensitivities
    omega_full = np.array(
        [
            [0.04, 0.01, -0.005],  # Eq
            [0.01, 0.02, 0.002],  # FX
            [-0.005, 0.002, 0.01],  # IR
        ]
    )

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
