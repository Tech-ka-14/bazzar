import numpy as np

def kolmogorov_smirnoff_statistic(f1_cdf_values, f2_cdf_values):
    """
    Calculates the KS test statistic: the maximum vertical difference 
    between two cumulative distribution functions.
    """
    # Ensure inputs are numpy arrays
    f1 = np.array(f1_cdf_values)
    f2 = np.array(f2_cdf_values)
    
    ks_stat = np.max(np.abs(f1 - f2))
    return ks_stat

def anderson_darling_statistic(f_empirical_values, f_hypothesized_values):
    """
    Calculates the specific AD statistic defined in the text, 
    designed to emphasize tail fit.
    """
    f_e = np.array(f_empirical_values)
    f_h = np.array(f_hypothesized_values)
    
    # Avoid division by zero at the extreme edges (where F(x) = 0 or 1)
    # by adding a tiny epsilon if necessary, though true CDFs evaluated 
    # strictly strictly inside the bounds usually avoid this.
    epsilon = 1e-10
    f_h_clamped = np.clip(f_h, epsilon, 1 - epsilon)
    
    numerator = np.abs(f_e - f_h_clamped)
    denominator = np.sqrt(f_h_clamped * (1 - f_h_clamped))
    
    ad_stat = np.max(numerator / denominator)
    return ad_stat