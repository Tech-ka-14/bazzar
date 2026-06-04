import numpy as np
import scipy.stats as stats

def normal_confidence_interval_mean(sample_mean, pop_std, n, confidence_level=0.95):
    """
    Calculates a two-sided confidence interval for a population mean
    when the population variance is KNOWN.
    """
    alpha = 1 - ((1 - confidence_level) / 2)
    z_critical = stats.norm.ppf(alpha)
    margin_of_error = z_critical * (pop_std / np.sqrt(n))
    return sample_mean - margin_of_error, sample_mean + margin_of_error

def student_t_confidence_interval_mean(sample_mean, sample_std, n, confidence_level=0.95):
    """
    Calculates a two-sided confidence interval for a population mean
    when the population variance is UNKNOWN (estimated from sample).
    """
    degrees_of_freedom = n - 1
    alpha = 1 - ((1 - confidence_level) / 2)
    t_critical = stats.t.ppf(alpha, df=degrees_of_freedom)
    margin_of_error = t_critical * (sample_std / np.sqrt(n))
    return sample_mean - margin_of_error, sample_mean + margin_of_error

def chi_squared_confidence_interval_variance(sample_var, n, confidence_level=0.95):
    """
    Calculates a two-sided confidence interval for a population variance
    using the Chi-squared distribution.
    """
    degrees_of_freedom = n - 1
    lower_alpha = (1 - confidence_level) / 2
    upper_alpha = 1 - lower_alpha
    
    chi2_lower = stats.chi2.ppf(lower_alpha, df=degrees_of_freedom)
    chi2_upper = stats.chi2.ppf(upper_alpha, df=degrees_of_freedom)
    
    numerator = degrees_of_freedom * sample_var
    return numerator / chi2_upper, numerator / chi2_lower

# Recreating Example I.3.14 (Confidence Interval for a Population Mean)
print("Example I.3.14 - 99% CI for Mean:")
lower, upper = student_t_confidence_interval_mean(sample_mean=8, sample_std=2, n=11, confidence_level=0.99)
print(f"Lower Bound: {lower:.2f}, Upper Bound: {upper:.2f}") # Expected: [6.09, 9.91]