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
if __name__ == "__main__":
    # Hypothetical GPD parameters estimated from historical tail data
    var_99 = 100000.0   # 99% Value at Risk is $100,000
    scale_beta = 15000  # Scale parameter
    tail_xi = 0.2       # Tail index (heavy tailed, but finite mean)
    
    etl = calculate_expected_tail_loss(var_99, scale_beta, tail_xi)
    print("--- Generalized Pareto Distribution (GPD) ---")
    print(f"Value at Risk (VaR): ${var_99:,.2f}")
    print(f"Expected Tail Loss (ETL): ${etl:,.2f}")