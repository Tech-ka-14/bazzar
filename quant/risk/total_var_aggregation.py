"""Total VaR aggregation from systematic and specific components.

Assuming systematic and specific risks are uncorrelated, total VaR is the
square root of the sum of squared component VaRs (Alexander 2008, Market
Risk Analysis IV, Section IV.2.2).
"""

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
    total_var = math.sqrt((systematic_var**2) + (specific_var**2))
    return total_var


def compute(systematic_var: float, specific_var: float) -> dict:
    """Standard facade: aggregate systematic and specific VaR into total VaR.

    Returns:
    dict: {"systematic_var", "specific_var", "total_var"}.
    """
    total_var = calculate_total_var(float(systematic_var), float(specific_var))
    return {
        "systematic_var": float(systematic_var),
        "specific_var": float(specific_var),
        "total_var": float(total_var),
    }


if __name__ == "__main__":
    # Example Usage
    sys_var = 250_000  # $250k Systematic VaR
    spec_var = 75_000  # $75k Specific VaR

    total_var = calculate_total_var(sys_var, spec_var)
    print(f"Total Aggregated VaR: ${total_var:,.2f}")
