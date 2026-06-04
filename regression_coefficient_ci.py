import numpy as np
import scipy.stats as stats

def coefficient_confidence_interval(beta_hat, standard_error, df, confidence_level=0.95):
    """
    Calculates the confidence interval for a regression coefficient.
    
    Parameters:
    beta_hat (float): The estimated coefficient.
    standard_error (float): The estimated standard error of the coefficient.
    df (int): Degrees of freedom (T - k).
    confidence_level (float): The desired confidence level (e.g., 0.95 for 95%).
    
    Returns:
    tuple: (lower_bound, upper_bound)
    """
    # Calculate the tail probability (alpha / 2)
    alpha = 1.0 - confidence_level
    q = 1.0 - (alpha / 2.0)
    
    # Get the critical t-value
    t_critical = stats.t.ppf(q, df)
    
    # Calculate the margin of error
    margin_of_error = t_critical * standard_error
    
    # Calculate bounds
    lower_bound = beta_hat - margin_of_error
    upper_bound = beta_hat + margin_of_error
    
    return lower_bound, upper_bound

# --- Example I.4.10 Implementation ---
if __name__ == "__main__":
    beta_gold = 0.1709
    se_gold = 0.0297  # Derived from sqrt(8.82239e-2)
    degrees_of_freedom = 569
    
    lower, upper = coefficient_confidence_interval(beta_gold, se_gold, degrees_of_freedom, 0.95)
    print(f"95% Confidence Interval for Gold Coefficient: [{lower:.4f}, {upper:.4f}]")