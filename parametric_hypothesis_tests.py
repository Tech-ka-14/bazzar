import numpy as np
import scipy.stats as stats

def one_sample_t_test(sample_mean, pop_mean_h0, sample_std, n):
    """
    Calculates the test statistic for a one-sample test on the mean.
    Formula from text: t = (X_bar - mu) / s
    Note: 's' in the text's example represents the standard error of the mean.
    """
    t_stat = (sample_mean - pop_mean_h0) / sample_std
    return t_stat

def two_sample_t_test_means(mean1, mean2, var1, var2, n1, n2):
    """
    Calculates the t-statistic to test the equality of two means.
    """
    standard_error = np.sqrt((var1 / n1) + (var2 / n2))
    t_stat = (mean1 - mean2) / standard_error
    return t_stat

def one_sample_chi2_test_variance(sample_var, pop_var_h0, n):
    """
    Calculates the Chi-squared statistic to test a single variance.
    """
    chi2_stat = ((n - 1) * sample_var) / pop_var_h0
    return chi2_stat

def two_sample_f_test_variances(var1, var2, n1, n2):
    """
    Calculates the F-statistic to test the equality of two variances.
    """
    f_stat = var1 / var2
    
    # Calculate the p-value for the lower tail as per Example I.3.15
    p_value = stats.f.cdf(f_stat, dfn=n1-1, dfd=n2-1)
    return f_stat, p_value

# --- Recreating Example I.3.15: Testing for Equality of Means and Variances ---
# Sample 1 stats
n1, mean1, var1 = 25, 1.0, 3.0
# Sample 2 stats
n2, mean2, var2 = 35, 2.0, 8.0

print("Example I.3.15 Results:")
f_stat, f_p_val = two_sample_f_test_variances(var1, var2, n1, n2)
print(f"F-Statistic (Variances): {f_stat:.3f}") # Expected: 0.375
print(f"F-Test P-Value (lower tail): {f_p_val:.4f}") # Expected: ~0.007

t_stat = two_sample_t_test_means(mean1, mean2, var1, var2, n1, n2)
print(f"t-Statistic (Means): {t_stat:.3f}") # Expected: -1.697