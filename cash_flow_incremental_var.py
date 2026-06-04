import numpy as np
from scipy.stats import norm

# Setup Example IV.2.4
h_days = 10
z_score = norm.ppf(0.99) # 2.32635 for 1% VaR

# 1-day Covariance Matrix in basis points squared
omega_1 = np.array([
    [22.5, 17.1, 13.5],
    [17.1, 14.4, 11.7],
    [13.5, 11.7, 10.0]
])
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