"""Analytic expected tail loss under a GPD tail model.

Given a GPD-based VaR, the analytic ETL is VaR plus the GPD mean excess
loss over the VaR threshold.
Reference: Alexander (2008), Market Risk Analysis IV, Equation IV.3.20,
Example IV.3.6.2.
"""


def calculate_gpd_etl(var_alpha: float, beta: float, xi: float) -> float:
    """
    Calculates the analytic Expected Tail Loss under a Generalized Pareto Distribution.
    (Equation IV.3.20)

    Parameters:
    var_alpha (float): The GPD VaR calculated previously (expressed as a positive loss).
    beta (float): The scale parameter of the fitted GPD.
    xi (float): The tail index (shape parameter) of the fitted GPD.

    Returns:
    float: The GPD Expected Tail Loss (ETL).
    """
    if xi >= 1:
        raise ValueError("Tail index (xi) must be < 1 for the expected mean to exist.")

    mean_excess_loss = (beta + (xi * var_alpha)) / (1.0 - xi)
    etl_alpha = var_alpha + mean_excess_loss

    return etl_alpha


# Example IV.3.6.2: Using the 10% threshold GPD data from Table IV.3.21


def compute(var_alpha: float, beta: float, xi: float) -> dict:
    """Standard facade: analytic GPD ETL as a JSON-serializable dict.

    Parameters:
    var_alpha (float): GPD VaR expressed as a positive loss (non-negative).
    beta (float): GPD scale parameter (positive, same units as var_alpha).
    xi (float): GPD tail index, must be < 1 for a finite mean.

    Returns:
    dict: {"method", "var", "etl"}.
    """
    if var_alpha < 0:
        raise ValueError("var_alpha must be a non-negative loss")
    if beta <= 0:
        raise ValueError("beta must be positive")

    etl = calculate_gpd_etl(float(var_alpha), float(beta), float(xi))
    return {"method": "gpd_parametric_etl", "var": float(var_alpha), "etl": float(etl)}


if __name__ == "__main__":
    gpd_var_01 = 0.0337  # 3.37% GPD VaR
    gpd_beta = 3.3786  # Scale parameter (Note: assumes scaled inputs from Table IV.3.21 context)
    gpd_xi = -0.1870  # Tail index

    # To utilize the normalized beta with percentage VaR, they must be on the same scale.
    # Assuming normalized beta mapped back to percentage terms:
    normalized_beta_pct = gpd_beta * 0.01

    gpd_etl = calculate_gpd_etl(gpd_var_01, normalized_beta_pct, gpd_xi)

    print(f"1% Parametric GPD VaR: {gpd_var_01:.2%}")
    print(f"1% Parametric GPD ETL: {gpd_etl:.2%}")
