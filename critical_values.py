import scipy.stats as stats

def get_normal_critical_value(alpha):
    """
    Calculates the critical value for a Standard Normal distribution.
    Matches the text's inverse standard normal function phi^-1(alpha).
    """
    return stats.norm.ppf(alpha)

def get_student_t_critical_value(alpha, degrees_of_freedom):
    """
    Calculates the critical value for a Student t distribution.
    Replaces the text's complex Excel TINV workaround.
    """
    return stats.t.ppf(alpha, df=degrees_of_freedom)

def get_chi_squared_critical_value(alpha, degrees_of_freedom):
    """
    Calculates the critical value for a Chi-squared distribution.
    """
    return stats.chi2.ppf(alpha, df=degrees_of_freedom)

# Example I.3.13 / I.3.14 Recreations:
print(f"Normal 97.5% Critical Value: {get_normal_critical_value(0.975):.4f}") # Expected: 1.9600
print(f"Student t 99.5% Critical Value (df=10): {get_student_t_critical_value(0.995, 10):.4f}") # Expected: 3.1693