"""Aggregation of economic capital and RAROC.

Diversified firm-wide economic capital is EC = sqrt(E' C E) where E is the
vector of stand-alone economic capitals and C their correlation matrix;
RAROC = expected return / economic capital.
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.6.2.
"""

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


def compute(ec_array, correlation_matrix, expected_return: float = None) -> dict:
    """Standard facade: diversified economic capital and RAROC as a JSON dict.

    Parameters:
    ec_array: 1-D array-like of stand-alone economic capitals.
    correlation_matrix: Square correlation matrix matching len(ec_array).
    expected_return (float, optional): Firm-wide expected return; when
    given, the RAROC is included in the result.

    Returns:
    dict: {"method", "n", "undiversified_ec", "diversified_ec",
    "diversification_benefit", "raroc"} ("raroc" only if expected_return
    is provided).
    """
    ec = np.asarray(ec_array, dtype=float).ravel()
    corr = np.asarray(correlation_matrix, dtype=float)
    if ec.size == 0:
        raise ValueError("ec_array must contain at least one entry")
    if corr.shape != (ec.size, ec.size):
        raise ValueError("correlation_matrix must be square with size len(ec_array)")

    ec_div = calculate_diversified_ec(ec, corr)
    result = {
        "method": "diversified_ec",
        "n": int(ec.size),
        "undiversified_ec": float(np.sum(ec)),
        "diversified_ec": float(ec_div),
        "diversification_benefit": float(np.sum(ec) - ec_div),
    }
    if expected_return is not None:
        result["raroc"] = float(calculate_raroc(float(expected_return), ec_div))
    return result


if __name__ == "__main__":
    ec_a = 40.0
    ec_b = 50.0
    ec_array = np.array([ec_a, ec_b])

    # Assume Expected Returns for Unit A and Unit B (in millions)
    return_a = 8.0
    return_b = 12.0

    # 1. Undiversified Firm (Assuming perfect correlation rho = 1.0)
    corr_perfect = np.array([[1.0, 1.0], [1.0, 1.0]])
    ec_undiversified = calculate_diversified_ec(ec_array, corr_perfect)  # Effectively 40 + 50 = 90

    # 2. Diversified Firm (Assuming actual correlation rho = 0.25)
    rho = 0.25
    corr_actual = np.array([[1.0, rho], [rho, 1.0]])
    ec_diversified = calculate_diversified_ec(ec_array, corr_actual)

    # 3. Calculate Firm RAROC
    firm_return = return_a + return_b
    undiversified_raroc = calculate_raroc(firm_return, ec_undiversified)
    diversified_raroc = calculate_raroc(firm_return, ec_diversified)

    print(f"Undiversified EC: ${ec_undiversified:.2f}M | RAROC: {undiversified_raroc * 100:.2f}%")
    print(f"Diversified EC: ${ec_diversified:.2f}M | RAROC: {diversified_raroc * 100:.2f}%")
