"""Mean excess loss and expected tail loss under a GPD tail model.

For a Generalized Pareto Distribution with scale beta and tail index xi,
the mean excess loss over threshold u is e(u) = (beta + xi u)/(1 - xi)
and ETL = VaR + e(VaR).
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.3.
"""


def calculate_mean_excess_loss(beta, xi, threshold_u):
    """
    Calculates the mean excess loss e(u) over a threshold u for a GPD.
    Formula: e(u) = (beta + xi * u) / (1 - xi)
    """
    if xi >= 1:
        raise ValueError("Tail index (xi) must be less than 1 for finite mean.")

    mean_excess = (beta + xi * threshold_u) / (1 - xi)
    return mean_excess


def calculate_expected_tail_loss(var_estimate, beta, xi):
    """
    Calculates the Expected Tail Loss (ETL) / Conditional VaR.
    Formula: ETL = VaR + e(VaR)
    """
    # Here the threshold u is the VaR estimate
    mean_excess_over_var = calculate_mean_excess_loss(beta, xi, threshold_u=var_estimate)

    etl = var_estimate + mean_excess_over_var
    return etl


# --- Example Usage ---


def compute(var_estimate: float, beta: float, xi: float) -> dict:
    """Standard facade: GPD expected tail loss as a JSON-serializable dict.

    Parameters:
    var_estimate (float): VaR expressed as a positive loss (non-negative).
    beta (float): GPD scale parameter (positive).
    xi (float): GPD tail index, must be < 1 for a finite mean.

    Returns:
    dict: {"method", "var", "etl", "mean_excess_loss"}.
    """
    if var_estimate < 0:
        raise ValueError("var_estimate must be a non-negative loss")
    if beta <= 0:
        raise ValueError("beta must be positive")

    etl = calculate_expected_tail_loss(float(var_estimate), float(beta), float(xi))
    mel = calculate_mean_excess_loss(float(beta), float(xi), float(var_estimate))
    return {
        "method": "gpd_etl",
        "var": float(var_estimate),
        "etl": float(etl),
        "mean_excess_loss": float(mel),
    }


if __name__ == "__main__":
    # Hypothetical GPD parameters estimated from historical tail data
    var_99 = 100000.0  # 99% Value at Risk is $100,000
    scale_beta = 15000  # Scale parameter
    tail_xi = 0.2  # Tail index (heavy tailed, but finite mean)

    etl = calculate_expected_tail_loss(var_99, scale_beta, tail_xi)
    print("--- Generalized Pareto Distribution (GPD) ---")
    print(f"Value at Risk (VaR): ${var_99:,.2f}")
    print(f"Expected Tail Loss (ETL): ${etl:,.2f}")
