import numpy as np
import scipy.stats as stats

def distribution_likelihood_ratio_test(z_series: np.ndarray) -> tuple:
    """
    Performs a Likelihood Ratio test to check if the transformed probabilities 
    Z_ht follow a Standard Normal N(0,1) distribution.
    """
    T = len(z_series)
    mu_hat = np.mean(z_series)
    sigma_hat = np.std(z_series, ddof=0)
    
    # Calculate the test statistic (Eq IV.6.42)
    sum_z_squared = np.sum(z_series**2)
    sum_standardized_squared = np.sum(((z_series - mu_hat) / sigma_hat)**2)
    
    lr_statistic = sum_z_squared - sum_standardized_squared - (T * np.log(sigma_hat**2))
    
    # Distributed as Chi-Squared with 2 degrees of freedom
    p_value = 1 - stats.chi2.cdf(lr_statistic, df=2)
    
    return lr_statistic, p_value