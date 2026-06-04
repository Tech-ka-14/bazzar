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
gpd_var_01 = 0.0337     # 3.37% GPD VaR
gpd_beta = 3.3786       # Scale parameter (Note: assumes scaled inputs from Table IV.3.21 context)
gpd_xi = -0.1870        # Tail index

# To utilize the normalized beta with percentage VaR, they must be on the same scale.
# Assuming normalized beta mapped back to percentage terms:
normalized_beta_pct = gpd_beta * 0.01 

gpd_etl = calculate_gpd_etl(gpd_var_01, normalized_beta_pct, gpd_xi)

print(f"1% Parametric GPD VaR: {gpd_var_01:.2%}")
print(f"1% Parametric GPD ETL: {gpd_etl:.2%}")