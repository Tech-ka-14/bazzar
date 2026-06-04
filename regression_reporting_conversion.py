def calculate_se_from_t_ratio(coefficient, t_ratio):
    """
    Calculates the estimated standard error of a coefficient 
    given the coefficient estimate and its t-ratio (for H0: beta = 0).
    """
    if t_ratio == 0:
        raise ValueError("t-ratio cannot be zero when calculating standard error.")
    return coefficient / t_ratio

def calculate_t_ratio_from_se(coefficient, standard_error):
    """
    Calculates the t-ratio (for H0: beta = 0) given the 
    coefficient estimate and its estimated standard error.
    """
    if standard_error == 0:
        raise ValueError("Standard error cannot be zero.")
    return coefficient / standard_error

def print_reported_regression(intercept, slope, intercept_stat, slope_stat, stat_name="t-ratio"):
    """
    Prints the estimated regression model in standard academic format,
    with the chosen statistic in parentheses below the coefficients.
    """
    print(f"Y_hat = {intercept:.1f} + {slope:.1f} X")
    print(f"       ({intercept_stat:.3f})   ({slope_stat:.3f})   <- ({stat_name}s)")
    print("-" * 45)


# --- Recreating the Reporting Example from the Text ---

# Given Data
intercept_est = 8.5
slope_est = 2.5

# Given Standard Errors
se_intercept = 2.053
se_slope = 0.619

# 1. Calculate the t-ratios from the Standard Errors
t_intercept = calculate_t_ratio_from_se(intercept_est, se_intercept)
t_slope = calculate_t_ratio_from_se(slope_est, se_slope)

print("Reporting with t-ratios:")
print_reported_regression(intercept_est, slope_est, t_intercept, t_slope, stat_name="t-ratio")
# Expected Output: Y_hat = 8.5 + 2.5 X \n (4.140) (4.039)
# Note: Slight rounding differences occur vs the text's (4.139) and (4.038) due to 
# the truncation of the inputs 2.053 and 0.619 in the text example.

# 2. Calculate the Standard Errors back from the calculated t-ratios
se_intercept_derived = calculate_se_from_t_ratio(intercept_est, t_intercept)
se_slope_derived = calculate_se_from_t_ratio(slope_est, t_slope)

print("Reporting with Standard Errors:")
print_reported_regression(intercept_est, slope_est, se_intercept_derived, se_slope_derived, stat_name="standard error")
# Expected Output: Y_hat = 8.5 + 2.5 X \n (2.053) (0.619)