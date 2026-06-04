import numpy as np

def calculate_specific_var(total_var: float, systematic_var: float) -> float:
    """
    Derives Specific VaR from Total and Systematic VaR, assuming the correlation 
    between residual and market returns is exactly zero (Equation IV.2.47).
    """
    if systematic_var > total_var:
        raise ValueError("Systematic VaR cannot exceed Total VaR under orthogonal assumptions.")
        
    return np.sqrt((total_var ** 2) - (systematic_var ** 2))

# Example IV.2.13: Disaggregation of VaR
total_portfolio_value = 20_000_000 # $20m
total_volatility = 0.25            # 25% portfolio volatility
systematic_var = 1_973_824         # Calculated from Example IV.2.12

# 1. Calculate Total VaR based on total volatility
from scipy.stats import norm
z_score = norm.ppf(0.99)
total_var = z_score * total_volatility * np.sqrt(1/12) * total_portfolio_value

# 2. Extract Specific VaR
specific_var = calculate_specific_var(total_var, systematic_var)

print(f"Total Portfolio VaR: ${total_var:,.0f}")
print(f"Systematic VaR (Factor Driven): ${systematic_var:,.0f}")
print(f"Specific VaR (Idiosyncratic): ${specific_var:,.0f}")