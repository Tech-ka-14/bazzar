"""Incremental VaR of new cash flows via the DelVaR gradient.

The DelVaR gradient of a normal linear portfolio is
(z / sigma) * Omega * theta; the incremental VaR of a new trade is the
element-wise product of its cash-flow sensitivities with that gradient.
Reference: Alexander (2008), Market Risk Analysis IV, Example IV.2.4.
"""


def compute(theta, omega_1d, delta_theta, h_days: int = 10, alpha: float = 0.01) -> dict:
    """Standard facade: incremental VaR of a new trade as a JSON dict.

    Parameters:
    theta: 1-D array-like of initial portfolio sensitivities.
    omega_1d: Square 1-day covariance matrix matching len(theta).
    delta_theta: 1-D array-like of the new trade's sensitivities.
    h_days (int): Risk horizon in days (covariance is scaled linearly).
    alpha (float): Tail probability in (0, 1), e.g. 0.01.

    Returns:
    dict: {"method", "alpha", "h_days", "initial_var",
    "total_incremental_var", "incremental_components"}.
    """
    import numpy as np
    from scipy.stats import norm

    theta = np.asarray(theta, dtype=float).ravel()
    omega = np.asarray(omega_1d, dtype=float)
    delta = np.asarray(delta_theta, dtype=float).ravel()
    if theta.size == 0:
        raise ValueError("theta must contain at least one sensitivity")
    if omega.shape != (theta.size, theta.size):
        raise ValueError("omega_1d must be square with size len(theta)")
    if delta.size != theta.size:
        raise ValueError("delta_theta must have the same length as theta")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    z_score = norm.ppf(1 - alpha)
    omega_h = omega * int(h_days)
    variance = theta.T @ omega_h @ theta
    volatility = np.sqrt(variance)
    initial_var = z_score * volatility
    gradient = (z_score / volatility) * (omega_h @ theta)
    components = delta * gradient

    return {
        "method": "incremental_var",
        "alpha": float(alpha),
        "h_days": int(h_days),
        "initial_var": float(initial_var),
        "total_incremental_var": float(np.sum(components)),
        "incremental_components": [float(x) for x in components],
    }


if __name__ == "__main__":
    import numpy as np
    from scipy.stats import norm

    # Setup Example IV.2.4
    h_days = 10
    z_score = norm.ppf(0.99)  # 2.32635 for 1% VaR

    # 1-day Covariance Matrix in basis points squared
    omega_1 = np.array([[22.5, 17.1, 13.5], [17.1, 14.4, 11.7], [13.5, 11.7, 10.0]])
    omega_10 = omega_1 * h_days

    # Initial Portfolio Sensitivities (theta)
    theta_init = np.array([1000, 1500, 2000])

    # 1. Calculate the initial portfolio volatility and VaR
    portfolio_variance = theta_init.T @ omega_10 @ theta_init
    portfolio_volatility = np.sqrt(portfolio_variance)
    initial_var = z_score * portfolio_volatility

    print(f"Initial 1% 10-day VaR: ${initial_var:,.0f}")

    # 2. Calculate the DelVaR Gradient
    gradient_vector = (z_score / portfolio_volatility) * (omega_10 @ theta_init)
    print(f"DelVaR Gradient: {gradient_vector.round(4)}")

    # 3. New Swap Trade Sensitivities (Delta Theta calculated via exact PV01)
    delta_theta = np.array([277.3935, -525.8534, -61.7144])

    # 4. Calculate Incremental VaR Components (Element-wise multiplication)
    incremental_components = delta_theta * gradient_vector
    total_incremental_var = np.sum(incremental_components)

    print("\n--- Incremental VaR Impact ---")
    print(f"Year 1 Cash Flow Impact: ${incremental_components[0]:,.0f}")
    print(f"Year 2 Cash Flow Impact: ${incremental_components[1]:,.0f}")
    print(f"Year 3 Cash Flow Impact: ${incremental_components[2]:,.0f}")
    print(f"Total Incremental VaR: ${total_incremental_var:,.0f}")
