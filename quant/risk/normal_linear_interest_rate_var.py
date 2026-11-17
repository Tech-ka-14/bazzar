"""Normal linear interest-rate VaR of a cash-flow map.

VaR of a portfolio mapped to PV01 sensitivities theta against an annual
covariance matrix of interest-rate changes: VaR = Z * sqrt(theta' Omega_h
theta).
Reference: Alexander (2008), Market Risk Analysis IV, Formula IV.1.28,
Example IV.1.8.
"""

import numpy as np
from scipy.stats import norm


def calculate_interest_rate_var(
    theta: np.ndarray,
    omega_annual: np.ndarray,
    horizon_days: int,
    confidence_level: float,
    days_in_year: int = 250,
):
    """
    Calculates the Normal Linear Interest Rate VaR for a cash flow map.

    Parameters:
    theta (np.ndarray): The vector of risk factor sensitivities (PV01s).
    omega_annual (np.ndarray): The annual covariance matrix of interest rate changes (in basis points).
    horizon_days (int): The VaR risk horizon in days (h).
    confidence_level (float): The confidence level (e.g., 0.99 for 1% significance).
    days_in_year (int): Trading days in a year to scale the covariance matrix.

    Returns:
    tuple: (Interest Rate VaR, Scaled Covariance Matrix, Portfolio Standard Deviation)
    """
    # Scale the annual covariance matrix to the h-day horizon
    time_fraction = horizon_days / days_in_year
    omega_h = omega_annual * time_fraction

    # Calculate portfolio variance using the quadratic form: theta.T * Omega_h * theta
    portfolio_variance = theta.T @ omega_h @ theta

    # Calculate portfolio standard deviation (in value terms)
    portfolio_std_dev = np.sqrt(portfolio_variance)

    # Calculate standard normal critical value
    alpha = 1.0 - confidence_level
    critical_value = norm.ppf(1 - alpha)

    # Calculate the Interest Rate VaR (Formula IV.1.28)
    interest_rate_var = critical_value * portfolio_std_dev

    return interest_rate_var, omega_h, portfolio_std_dev


# Example IV.1.8: Normal VaR of a Simple Cash Flow
# 1. Define the PV01 vector (theta) for 1-year and 2-year vertices


def compute(theta, omega_annual, horizon_days: int = 10, confidence: float = 0.99) -> dict:
    """Standard facade: normal linear interest-rate VaR as a JSON dict.

    Parameters:
    theta: 1-D array-like of PV01 sensitivities.
    omega_annual: Square annual covariance matrix (basis points squared)
    matching len(theta).
    horizon_days (int): Risk horizon in days.
    confidence (float): Confidence level in (0, 1), e.g. 0.99.

    Returns:
    dict: {"method", "confidence", "horizon_days", "var", "std_dev"}
    with positive monetary values.
    """
    theta = np.asarray(theta, dtype=float).ravel()
    omega = np.asarray(omega_annual, dtype=float)
    if theta.size == 0:
        raise ValueError("theta must contain at least one sensitivity")
    if omega.shape != (theta.size, theta.size):
        raise ValueError("omega_annual must be square with size len(theta)")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in the open interval (0, 1)")

    var, _, std_dev = calculate_interest_rate_var(
        theta, omega, int(horizon_days), float(confidence)
    )
    return {
        "method": "normal_linear_interest_rate",
        "confidence": float(confidence),
        "horizon_days": int(horizon_days),
        "var": float(var),
        "std_dev": float(std_dev),
    }


if __name__ == "__main__":
    theta_vector = np.array([50.0, 75.0])

    # 2. Construct the Annual Covariance Matrix (Omega)
    vol_1yr = 100.0  # Volatility of 1-year rate in basis points
    vol_2yr = 80.0  # Volatility of 2-year rate in basis points
    correlation = 0.9

    covariance_12 = correlation * vol_1yr * vol_2yr

    omega_annual_matrix = np.array([[vol_1yr**2, covariance_12], [covariance_12, vol_2yr**2]])

    # 3. VaR Parameters
    h_days = 10
    conf_lvl = 0.99

    # Execute calculation
    var_10d, omega_10d, std_dev = calculate_interest_rate_var(
        theta=theta_vector,
        omega_annual=omega_annual_matrix,
        horizon_days=h_days,
        confidence_level=conf_lvl,
    )

    print(f"10-day Covariance Matrix (Omega_10):\n{omega_10d}\n")
    print(f"10-day Portfolio Standard Deviation: ${std_dev:,.2f}")
    print(f"1% 10-day Interest Rate VaR: ${var_10d:,.0f}")
