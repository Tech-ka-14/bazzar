import numpy as np

def calculate_portfolio_pnl(pv01_vector, rate_changes):
    """
    Calculates the Profit and Loss (P&L) of an interest-rate-sensitive 
    portfolio using its PV01 sensitivities.
    
    Parameters:
    pv01_vector (numpy.ndarray): 1D array of length n containing the Present 
                                 Value of a Basis Point for each yield curve vertex.
    rate_changes (numpy.ndarray): 1D array of length n containing the absolute 
                                  changes in the interest rates (in basis points).
                                  
    Returns:
    float: The estimated change in portfolio value (Delta P_t).
    """
    # The P&L is the dot product of the PV01 vector and the rate changes vector
    delta_P = np.dot(pv01_vector, rate_changes)
    return float(delta_P)

if __name__ == "__main__":
    # --- Example II.2.4.1 Implementation ---
    # Suppose a portfolio is mapped to 5 vertices: 1y, 2y, 3y, 4y, 5y
    # PV01 signifies the dollar change in value for a 1 basis point rate move
    pv01_exposures = np.array([-15000, -25000, 10000, 0, -40000])
    
    # Assume the interest rates moved today (in basis points)
    # E.g., short rates went up, long rates went down
    daily_rate_changes = np.array([2.5, 1.0, 0.0, -1.5, -3.0])
    
    pnl = calculate_portfolio_pnl(pv01_exposures, daily_rate_changes)
    
    print("--- Interest Rate Portfolio P&L ---")
    print(f"Estimated Daily P&L: ${pnl:,.2f}")
    if pnl > 0:
        print("(The portfolio gained value from today's yield curve shift.)")
    else:
        print("(The portfolio lost value from today's yield curve shift.)")