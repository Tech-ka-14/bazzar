import numpy as np
import scipy.stats as stats

def coefficient_standard_error(s, s_x, t_obs):
    """
    Calculates the estimated standard error of the slope coefficient (beta).
    
    Parameters:
    s : Standard error of the regression (residuals)
    s_x : Sample standard deviation of the explanatory variable
    t_obs : Number of observations (T)
    """
    return s / (s_x * np.sqrt(t_obs - 1))

def coefficient_t_test(beta_hat, beta_null, se_beta, t_obs, two_sided=True):
    """
    Calculates the t-statistic and p-value for a regression coefficient.
    
    Parameters:
    beta_hat : The estimated coefficient from the regression model
    beta_null : The hypothesized value of the coefficient (e.g., 0)
    se_beta : The estimated standard error of the coefficient
    t_obs : Number of observations (T)
    """
    # Degrees of freedom for a simple linear regression is T - 2
    df = t_obs - 2
    
    # Calculate the t-statistic
    t_stat = (beta_hat - beta_null) / se_beta
    
    # Calculate the p-value
    if two_sided:
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    else:
        # Assuming upper-tailed one-sided test as in Example I.4.5 part (b)
        p_value = 1 - stats.t.cdf(t_stat, df)
        
    return t_stat, p_value

# --- Recreating Example I.4.5 ---
T = 5
s = 1.958
s_x = 1.581
beta_hat = 2.5

# 1. Calculate standard error
se_beta = coefficient_standard_error(s, s_x, T)
print(f"Estimated Standard Error of Beta: {se_beta:.3f}") # Expected: ~0.619

# 2. Test (a): H0: beta = 1 (Two-sided)
t_stat_a, p_val_a = coefficient_t_test(beta_hat, beta_null=1, se_beta=se_beta, t_obs=T, two_sided=True)
print(f"Test (a) - t-statistic: {t_stat_a:.3f}, p-value: {p_val_a:.4f}")

# 3. Test (b): H0: beta = 0 (One-sided)
t_stat_b, p_val_b = coefficient_t_test(beta_hat, beta_null=0, se_beta=se_beta, t_obs=T, two_sided=False)
print(f"Test (b) - t-statistic: {t_stat_b:.3f}, p-value: {p_val_b:.4f}")