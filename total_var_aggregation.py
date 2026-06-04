import math

def calculate_total_var(systematic_var: float, specific_var: float):
    """
    Calculates the Total VaR assuming systematic and specific risks are uncorrelated.
    
    Parameters:
    systematic_var (float): The VaR captured by the risk factor mapping.
    specific_var (float): The residual VaR not captured by the mapping.
    
    Returns:
    float: Total aggregated VaR.
    """
    # Assuming zero correlation between systematic and specific risk
    total_var = math.sqrt((systematic_var ** 2) + (specific_var ** 2))
    return total_var

# Example Usage
sys_var = 250_000  # $250k Systematic VaR
spec_var = 75_000  # $75k Specific VaR

total_var = calculate_total_var(sys_var, spec_var)
print(f"Total Aggregated VaR: ${total_var:,.2f}")