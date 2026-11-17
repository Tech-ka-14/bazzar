"""Euler allocation of firm-wide economic capital.

Stand-alone and marginal VaR of business units under a multivariate
normal model; the Euler principle allocates the total firm economic
capital so that allocated contributions sum exactly to the total.
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.6.
"""

import numpy as np
import scipy.stats as stats


def calculate_stand_alone_ec(
    weights: np.ndarray, vols: np.ndarray, total_firm_value: float, alpha: float
) -> np.ndarray:
    """
    Calculates the Stand-Alone Economic Capital for each business unit.
    """
    z_score = stats.norm.ppf(1 - alpha)
    stand_alone_vars = z_score * vols
    return weights * stand_alone_vars * total_firm_value


def calculate_marginal_var(weights: np.ndarray, cov_matrix: np.ndarray, alpha: float) -> np.ndarray:
    """
    Calculates the Marginal VaR for each business unit assuming a multivariate normal distribution.
    """
    z_score = stats.norm.ppf(1 - alpha)

    # 1. Total firm variance and volatility
    firm_variance = weights.T @ cov_matrix @ weights
    firm_volatility = np.sqrt(firm_variance)

    # 2. Marginal Volatility is the derivative of firm vol with respect to weights
    marginal_volatility = (cov_matrix @ weights) / firm_volatility

    # 3. Marginal VaR
    marginal_var = z_score * marginal_volatility
    return marginal_var


def allocate_economic_capital(
    weights: np.ndarray, marginal_vars: np.ndarray, total_firm_value: float
) -> dict:
    """
    Allocates the firm-wide Economic Capital using the Euler principle.
    The sum of the allocated capital exactly equals the total firm Economic Capital.
    """
    # Component VaR (Risk Contribution percentage)
    component_var_pct = weights * marginal_vars

    # Absolute Allocated Capital
    allocated_capital = component_var_pct * total_firm_value

    total_firm_ec = np.sum(allocated_capital)

    return {"Allocated_Capital_per_Unit": allocated_capital, "Total_Firm_EC": total_firm_ec}


# --- Example Usage ---
# Suppose a firm has 3 Business Units: Equities, Fixed Income, and Commodities


def compute(weights, cov_matrix, total_firm_value: float = 1.0, alpha: float = 0.01) -> dict:
    """Standard facade: Euler economic-capital allocation as a JSON dict.

    Parameters:
    weights: 1-D array-like of business-unit weights.
    cov_matrix: Square covariance matrix matching len(weights).
    total_firm_value (float): Total firm value for monetary allocation.
    alpha (float): Tail probability in (0, 1), e.g. 0.01.

    Returns:
    dict: {"method", "alpha", "n", "marginal_vars", "allocated_capital",
    "total_firm_ec"}.
    """
    weights = np.asarray(weights, dtype=float).ravel()
    cov = np.asarray(cov_matrix, dtype=float)
    if weights.size == 0:
        raise ValueError("weights must contain at least one entry")
    if cov.shape != (weights.size, weights.size):
        raise ValueError("cov_matrix must be square with size len(weights)")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    marginal_vars = calculate_marginal_var(weights, cov, float(alpha))
    allocation = allocate_economic_capital(weights, marginal_vars, float(total_firm_value))
    return {
        "method": "euler_allocation",
        "alpha": float(alpha),
        "n": int(weights.size),
        "marginal_vars": [float(x) for x in marginal_vars],
        "allocated_capital": [float(x) for x in allocation["Allocated_Capital_per_Unit"]],
        "total_firm_ec": float(allocation["Total_Firm_EC"]),
    }


if __name__ == "__main__":
    weights = np.array([0.40, 0.40, 0.20])
    vols = np.array([0.25, 0.15, 0.30])

    # Subjective Correlation Matrix
    corr_matrix = np.array([[1.0, 0.2, 0.4], [0.2, 1.0, -0.1], [0.4, -0.1, 1.0]])

    # Convert to Covariance Matrix
    cov_matrix = np.outer(vols, vols) * corr_matrix

    # EC Parameters (99.97% Confidence for AA Rating, 1-Year Horizon)
    alpha = 0.0003
    firm_value = 1_000_000_000  # $1 Billion

    # 1. Calculate the Marginal VaRs
    marginal_vars = calculate_marginal_var(weights, cov_matrix, alpha)

    # 2. Perform the Euler Allocation
    allocation_results = allocate_economic_capital(weights, marginal_vars, firm_value)
