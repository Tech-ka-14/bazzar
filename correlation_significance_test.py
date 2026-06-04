import numpy as np
import scipy.stats as stats

def test_correlation_significance(rho_hat, T, alpha=0.05):
    """
    Tests whether a historical correlation estimate is significantly greater than 0.
    """
    # Calculate the t-statistic
    t_stat = (rho_hat * np.sqrt(T)) / np.sqrt(1 - rho_hat**2)
    
    # Calculate the critical t-value and p-value for a one-sided test
    t_critical = stats.t.ppf(1 - alpha, T)
    p_value = stats.t.sf(t_stat, T)
    
    reject_null = t_stat > t_critical
    
    return {
        "Correlation Estimate": rho_hat,
        "Observations (T)": T,
        "t-statistic": t_stat,
        "Critical t-value": t_critical,
        "p-value": p_value,
        "Significant (Reject H0)": reject_null
    }

# Example implementation based on Example II.3.11
test_result = test_correlation_significance(rho_hat=0.2, T=36, alpha=0.10)