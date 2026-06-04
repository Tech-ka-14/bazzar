import numpy as np

def calculate_gpd_var(u_loss: float, beta: float, xi: float, n_total: int, n_u: int, alpha: float) -> float:
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
    term_1 = beta / (xi * (n_total ** xi))
    term_2 = ((n_u / tail_prob) ** xi) - (n_total ** xi)
    
    var_alpha = u_loss + (term_1 * term_2)
    
    return var_alpha

# Example IV.3.3: Using the GPD to Estimate VaR at Extreme Quantiles
# Using the 10% threshold row from Table IV.3.10
# Note: The threshold return in the table is -1.1960. Since we model losses, the threshold is positive 1.1960.
threshold_loss = 1.1960
gpd_xi = -0.1870
gpd_beta = 3.3786
sample_total = 14264
exceedances = 1426
confidence_level = 0.99 # 99% VaR

normalized_var = calculate_gpd_var(
    u_loss=threshold_loss, 
    beta=gpd_beta, 
    xi=gpd_xi, 
    n_total=sample_total, 
    n_u=exceedances, 
    alpha=confidence_level
)

print(f"Normalized GPD VaR: {normalized_var:.4f}")
print("Note: To find the final Monetary/Percentage VaR, this normalized result must be multiplied by the portfolio's standard deviation and offset by its mean.")