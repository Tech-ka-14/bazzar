import numpy as np

def calculate_diversified_ec(ec_array: np.ndarray, correlation_matrix: np.ndarray) -> float:
    """
    Calculates the diversified firm-wide Economic Capital (EC) 
    given the stand-alone ECs and their correlation matrix.
    """
    # EC_firm = sqrt( E^T * C * E )
    variance_ec = ec_array.T @ correlation_matrix @ ec_array
    return np.sqrt(variance_ec)

def calculate_raroc(expected_return: float, economic_capital: float) -> float:
    """
    Calculates the Risk-Adjusted Return on Capital (RAROC).
    """
    return expected_return / economic_capital

# --- Example: Aggregation of Economic Capital (Two Units A and B) ---
# Assume Stand-Alone EC for Unit A and Unit B (in millions)
ec_a = 40.0
ec_b = 50.0
ec_array = np.array([ec_a, ec_b])

# Assume Expected Returns for Unit A and Unit B (in millions)
return_a = 8.0
return_b = 12.0

# 1. Undiversified Firm (Assuming perfect correlation rho = 1.0)
corr_perfect = np.array([[1.0, 1.0],
                         [1.0, 1.0]])
ec_undiversified = calculate_diversified_ec(ec_array, corr_perfect) # Effectively 40 + 50 = 90

# 2. Diversified Firm (Assuming actual correlation rho = 0.25)
rho = 0.25
corr_actual = np.array([[1.0, rho],
                        [rho, 1.0]])
ec_diversified = calculate_diversified_ec(ec_array, corr_actual)

# 3. Calculate Firm RAROC
firm_return = return_a + return_b
undiversified_raroc = calculate_raroc(firm_return, ec_undiversified)
diversified_raroc = calculate_raroc(firm_return, ec_diversified)

print(f"Undiversified EC: ${ec_undiversified:.2f}M | RAROC: {undiversified_raroc*100:.2f}%")
print(f"Diversified EC: ${ec_diversified:.2f}M | RAROC: {diversified_raroc*100:.2f}%")