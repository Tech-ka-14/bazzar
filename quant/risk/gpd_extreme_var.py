"""GPD estimate of VaR at extreme quantiles.

Uses a Generalized Pareto Distribution fitted above a loss threshold u
to extrapolate VaR beyond the sample range.
Reference: Alexander (2008), Market Risk Analysis IV, Equation IV.3.6,
Example IV.3.3.
"""


def calculate_gpd_var(
    u_loss: float, beta: float, xi: float, n_total: int, n_u: int, alpha: float
) -> float:
    """
    Calculates the VaR at an extreme quantile using the Generalized Pareto Distribution (GPD).
    Equation IV.3.6.

    Parameters:
    u_loss (float): The threshold for losses. (If the threshold is provided as a negative return, use its absolute value).
    beta (float): The scale parameter of the GPD.
    xi (float): The shape parameter (tail index) of the GPD.
    n_total (int): The total sample size.
    n_u (int): The number of observations exceeding the threshold.
    alpha (float): The confidence level (e.g., 0.999 for 99.9% VaR).

    Returns:
    float: The estimated VaR based on the GPD fit.
    """
    # The tail probability (e.g., 0.001 for 99.9% confidence)
    tail_prob = 1.0 - alpha

    # Calculate the components of Equation IV.3.6
    term_1 = beta / (xi * (n_total**xi))
    term_2 = ((n_u / tail_prob) ** xi) - (n_total**xi)

    var_alpha = u_loss + (term_1 * term_2)

    return var_alpha


# Example IV.3.3: Using the GPD to Estimate VaR at Extreme Quantiles
# Using the 10% threshold row from Table IV.3.10
# Note: The threshold return in the table is -1.1960. Since we model losses, the threshold is positive 1.1960.


def compute(
    u_loss: float, beta: float, xi: float, n_total: int, n_u: int, alpha: float = 0.99
) -> dict:
    """Standard facade: GPD extreme-quantile VaR as a JSON-serializable dict.

    Parameters:
    u_loss (float): Loss threshold (positive).
    beta (float): GPD scale parameter (positive).
    xi (float): GPD tail index (non-zero).
    n_total (int): Total sample size (positive).
    n_u (int): Number of exceedances above u (1 <= n_u <= n_total).
    alpha (float): Confidence level in (0, 1), e.g. 0.99.

    Returns:
    dict: {"method", "alpha", "var"}.
    """
    if u_loss <= 0 or beta <= 0:
        raise ValueError("u_loss and beta must be positive")
    if xi == 0:
        raise ValueError("xi must be non-zero for this parameterization")
    if n_total <= 0 or not 1 <= n_u <= n_total:
        raise ValueError("require n_total > 0 and 1 <= n_u <= n_total")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    var = calculate_gpd_var(
        float(u_loss), float(beta), float(xi), int(n_total), int(n_u), float(alpha)
    )
    return {"method": "gpd_extreme", "alpha": float(alpha), "var": float(var)}


if __name__ == "__main__":
    threshold_loss = 1.1960
    gpd_xi = -0.1870
    gpd_beta = 3.3786
    sample_total = 14264
    exceedances = 1426
    confidence_level = 0.99  # 99% VaR

    normalized_var = calculate_gpd_var(
        u_loss=threshold_loss,
        beta=gpd_beta,
        xi=gpd_xi,
        n_total=sample_total,
        n_u=exceedances,
        alpha=confidence_level,
    )

    print(f"Normalized GPD VaR: {normalized_var:.4f}")
    print(
        "Note: To find the final Monetary/Percentage VaR, this normalized result must be multiplied by the portfolio's standard deviation and offset by its mean."
    )
