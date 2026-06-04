import numpy as np
import statsmodels.api as sm
import scipy.stats as stats

def estimate_simple_linear_regression(y, x):
    """
    Fits an Ordinary Least Squares (OLS) regression model and 
    extracts the key metrics matching standard Excel/statistical output.
    """
    # In statsmodels, you must explicitly add a constant to fit an intercept
    x_with_constant = sm.add_constant(x)
    
    # Fit the OLS model
    model = sm.OLS(y, x_with_constant)
    results = model.fit()
    
    # --- 1. Goodness of Fit (Table I.4.5 Equivalents) ---
    r_squared = results.rsquared
    adj_r_squared = results.rsquared_adj
    standard_error = np.sqrt(results.mse_resid)
    observations = int(results.nobs)
    
    print(f"R-Squared: {r_squared:.4f}")
    print(f"Adjusted R-Squared: {adj_r_squared:.4f}")
    print(f"Standard Error: {standard_error:.4f}")
    print(f"Observations: {observations}")
    print("-" * 30)
    
    # --- 2. ANOVA (Table I.4.6 Equivalents) ---
    ess = results.ess # Explained Sum of Squares (Regression)
    rss = results.ssr # Residual Sum of Squares
    tss = results.centered_tss # Total Sum of Squares
    f_stat = results.fvalue
    
    print(f"Explained Sum of Squares (ESS): {ess:.4f}")
    print(f"Residual Sum of Squares (RSS): {rss:.4f}")
    print(f"Total Sum of Squares (TSS): {tss:.4f}")
    print(f"F-Statistic: {f_stat:.4f}")
    print("-" * 30)
    
    # --- 3. Coefficient Estimates (Table I.4.7 Equivalents) ---
    # results.params contains [intercept, slope]
    # results.bse contains standard errors
    # results.tvalues contains t-stats for H0: beta = 0
    # results.pvalues contains p-values
    
    print("Coefficients:")
    print(f"Intercept: {results.params[0]:.4f} (SE: {results.bse[0]:.4f}, t: {results.tvalues[0]:.4f}, p: {results.pvalues[0]:.4f})")
    print(f"Slope (Beta): {results.params[1]:.4f} (SE: {results.bse[1]:.4f}, t: {results.tvalues[1]:.4f}, p: {results.pvalues[1]:.4f})")
    
    return results

def custom_beta_hypothesis_test(beta_hat, standard_error, test_value=1.0, degrees_of_freedom=752):
    """
    Recreates the specific custom hypothesis test from the text:
    H0: beta = 1 vs H1: beta > 1
    """
    t_stat = (beta_hat - test_value) / standard_error
    
    # One-sided upper tail p-value
    p_value = 1 - stats.t.cdf(t_stat, df=degrees_of_freedom)
    
    return t_stat, p_value

# --- Recreating the Custom Hypothesis Test from the Text ---
print("\n--- Custom Hypothesis Test (H0: beta = 1 vs H1: beta > 1) ---")
# Using the values directly from Table I.4.7
estimated_beta = 1.2885
se_beta = 0.0427
df = 752 # 754 observations - 2 parameters

t_statistic, p_val = custom_beta_hypothesis_test(estimated_beta, se_beta, test_value=1.0, degrees_of_freedom=df)
print(f"Calculated t-statistic: {t_statistic:.4f}") # Expected: ~6.756 (Text rounds to 6.76)
print(f"P-value: {p_val:.6f}")
print("Result: Reject H0. There is evidence to suggest the stock has a market beta > 1.")