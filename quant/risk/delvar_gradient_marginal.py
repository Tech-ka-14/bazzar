"""DelVaR gradient, marginal (component) VaR and incremental VaR.

For the normal linear model with positions theta and covariance matrix
Omega, the DelVaR gradient is z_{1-alpha} * (Omega theta) / sqrt(theta'
Omega theta) (Equation IV.2.24, Alexander 2008). Marginal VaR components are
theta_i * grad_i and sum to the total VaR; incremental VaR of a trade is the
gradient inner product with the trade vector (Equations IV.2.22-IV.2.23).
"""

import numpy as np
from scipy.stats import norm


def calculate_delvar_gradient(
    theta: np.ndarray, omega_h: np.ndarray, alpha: float = 0.01
) -> np.ndarray:
    """
    Calculates the gradient vector (DelVaR) of the normal linear VaR.
    Equation IV.2.24.
    """
    critical_value = norm.ppf(1 - alpha)

    # Calculate portfolio variance and volatility
    variance = theta.T @ omega_h @ theta
    volatility = np.sqrt(variance)

    # Calculate the gradient: Z * (Omega * theta) * (1 / volatility)
    gradient = critical_value * (omega_h @ theta) * (1.0 / volatility)

    return gradient


def calculate_marginal_and_incremental_var(
    theta: np.ndarray, delta_theta: np.ndarray, omega_h: np.ndarray, alpha: float = 0.01
):
    """
    Calculates Marginal VaR components and Incremental VaR using the DelVaR gradient.
    Equations IV.2.22 and IV.2.23.
    """
    # 1. Get the gradient vector
    gradient = calculate_delvar_gradient(theta, omega_h, alpha)

    # 2. Marginal VaR components: Element-wise multiplication of theta and gradient
    marginal_var_components = theta * gradient

    # 3. Incremental VaR for a specific trade (delta_theta)
    incremental_var = delta_theta.T @ gradient

    return marginal_var_components, incremental_var


def compute(positions, cov_matrix, confidence: float = 0.99, trade=None) -> dict:
    """Standard facade: marginal/component VaR decomposition as a JSON dict.

    Parameters:
    positions: 1-D array-like of nominal positions/sensitivities per asset.
    cov_matrix: 2-D covariance matrix of the risk factors (array-like).
    confidence (float): Confidence level in (0, 1), e.g. 0.99.
    trade: optional 1-D array-like trade vector; when given, its first-order
    incremental VaR is included.

    Returns:
    dict: {"confidence", "gradient", "component_var", "total_var",
    "incremental_var" (only when trade is given)}. The component VaRs sum to
    total_var (Euler decomposition).
    """
    positions = np.asarray(positions, dtype=float).ravel()
    cov_matrix = np.asarray(cov_matrix, dtype=float)
    if cov_matrix.shape != (positions.size, positions.size):
        raise ValueError("cov_matrix must be square with side len(positions)")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in the open interval (0, 1)")

    alpha = 1.0 - float(confidence)
    gradient = calculate_delvar_gradient(positions, cov_matrix, alpha)
    component_var = positions * gradient
    result = {
        "confidence": float(confidence),
        "gradient": [float(g) for g in gradient],
        "component_var": [float(c) for c in component_var],
        "total_var": float(np.sum(component_var)),
    }
    if trade is not None:
        trade = np.asarray(trade, dtype=float).ravel()
        if trade.size != positions.size:
            raise ValueError("trade must have the same length as positions")
        result["incremental_var"] = float(trade.T @ gradient)
    return result


if __name__ == "__main__":
    # Example Usage
    theta_initial = np.array([100.0, 50.0])  # Initial positions
    trade_vector = np.array([10.0, -5.0])  # Buying 10 of asset 1, selling 5 of asset 2
    omega = np.array([[0.04, 0.02], [0.02, 0.09]])

    marginals, incremental = calculate_marginal_and_incremental_var(
        theta_initial, trade_vector, omega
    )

    print(f"Marginal VaR Vector: {marginals}")
    print(f"Sum of Marginals (Total VaR): {np.sum(marginals):.4f}")
    print(f"Estimated Incremental VaR from Trade: {incremental:.4f}")
