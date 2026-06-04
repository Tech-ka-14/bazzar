import numpy as np
from scipy.stats import norm

def calculate_interest_rate_var(theta: np.ndarray, omega_annual: np.ndarray, 
                                horizon_days: int, confidence_level: float, 
                                days_in_year: int = 250):
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
theta_vector = np.array([50.0, 75.0])

# 2. Construct the Annual Covariance Matrix (Omega)
vol_1yr = 100.0  # Volatility of 1-year rate in basis points
vol_2yr = 80.0   # Volatility of 2-year rate in basis points
correlation = 0.9

covariance_12 = correlation * vol_1yr * vol_2yr

omega_annual_matrix = np.array([
    [vol_1yr**2, covariance_12],
    [covariance_12, vol_2yr**2]
])

# 3. VaR Parameters
h_days = 10
conf_lvl = 0.99

# Execute calculation
var_10d, omega_10d, std_dev = calculate_interest_rate_var(
    theta=theta_vector, 
    omega_annual=omega_annual_matrix, 
    horizon_days=h_days, 
    confidence_level=conf_lvl
)

print(f"10-day Covariance Matrix (Omega_10):\n{omega_10d}\n")
print(f"10-day Portfolio Standard Deviation: ${std_dev:,.2f}")
print(f"1% 10-day Interest Rate VaR: ${var_10d:,.0f}")