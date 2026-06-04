import numpy as np
import scipy.stats as stats

def restricted_ols_estimation(y_data, X_matrix, R_matrix, q_vector):
    """
    Performs Restricted Ordinary Least Squares (ROLS) using matrix algebra
    to test multiple linear restrictions of the form R*beta = q.
    """
    y = np.array(y_data)
    X = np.array(X_matrix)
    R = np.array(R_matrix)
    q = np.array(q_vector)
    
    T, k = X.shape
    p = R.shape[0] # Number of restrictions
    
    # --- 1. Estimate the Unrestricted Model ---
    X_prime_X = X.T @ X
    X_prime_X_inv = np.linalg.inv(X_prime_X)
    X_prime_y = X.T @ y
    
    beta_unrestricted = X_prime_X_inv @ X_prime_y
    
    y_hat_u = X @ beta_unrestricted
    residuals_u = y - y_hat_u
    rss_u = residuals_u.T @ residuals_u
    
    # --- 2. Estimate the Restricted Model (ROLS formula) ---
    # Penalty term = (X'X)^-1 * R' * [R * (X'X)^-1 * R']^-1 * (R*beta_U - q)
    
    term1 = X_prime_X_inv @ R.T
    term2 = np.linalg.inv(R @ X_prime_X_inv @ R.T)
    term3 = (R @ beta_unrestricted) - q
    
    adjustment = term1 @ term2 @ term3
    beta_restricted = beta_unrestricted - adjustment
    
    y_hat_r = X @ beta_restricted
    residuals_r = y - y_hat_r
    rss_r = residuals_r.T @ residuals_r
    
    # --- 3. Run the Exact F-Test (Equation I.4.48) ---
    df_numerator = p
    df_denominator = T - k
    
    f_stat = ((rss_r - rss_u) / p) / (rss_u / df_denominator)
    p_value = 1.0 - stats.f.cdf(f_stat, dfn=df_numerator, dfd=df_denominator)
    
    return {
        'beta_unrestricted': beta_unrestricted,
        'rss_unrestricted': rss_u,
        'beta_restricted': beta_restricted,
        'rss_restricted': rss_r,
        'f_statistic': f_stat,
        'p_value': p_value
    }

# --- Recreating the Matrix Setup from the Text ---
# The text defines a hypothesis:
# H0: beta_1 - beta_2 = 0
#     beta_1 + beta_3 = 0
#    -beta_1 + beta_2 + 2*beta_3 = 2

# This translates to the R matrix and q vector:
R = [
    [ 1, -1,  0],
    [ 1,  0,  1],
    [-1,  1,  2]
]
q = [0, 0, 2]

# Let's create some dummy data to run through the solver
np.random.seed(42)
T_obs = 100
X_dummy = np.random.normal(0, 1, (T_obs, 3))
# True model where beta = [1, 1, -1] (This perfectly satisfies H0)
Y_dummy = X_dummy @ np.array([1, 1, -1]) + np.random.normal(0, 0.5, T_obs)

print("--- Testing Multiple Linear Restrictions (R*beta = q) ---")
results = restricted_ols_estimation(Y_dummy, X_dummy, R, q)

print("\nUnrestricted Coefficients:")
print(np.round(results['beta_unrestricted'], 4))
print(f"Unrestricted RSS: {results['rss_unrestricted']:.4f}")

print("\nRestricted Coefficients (Forced to obey H0):")
print(np.round(results['beta_restricted'], 4))
print(f"Restricted RSS: {results['rss_restricted']:.4f}")

print(f"\nF-Statistic: {results['f_statistic']:.4f}")
print(f"P-Value: {results['p_value']:.4f}")

if results['p_value'] > 0.05:
    print("Conclusion: Fail to reject H0. The restrictions are statistically valid.")
else:
    print("Conclusion: Reject H0. The restrictions significantly harm the model fit.")