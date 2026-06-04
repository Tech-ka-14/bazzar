import numpy as np
import scipy.stats as stats

def kupiec_unconditional_coverage(n_obs: int, n_exceedances: int, alpha: float) -> tuple:
    """
    Calculates the Kupiec Unconditional Coverage test statistic.
    """
    pi_exp = alpha
    pi_obs = n_exceedances / n_obs
    n0 = n_obs - n_exceedances
    n1 = n_exceedances
    
    # Handle the edge case of 0 exceedances to avoid log(0)
    if n1 == 0:
        log_lr_uc = n0 * np.log(1 - pi_exp) - n0 * np.log(1 - pi_obs)
    else:
        log_lr_uc = (n1 * np.log(pi_exp) + n0 * np.log(1 - pi_exp)) - \
                    (n1 * np.log(pi_obs) + n0 * np.log(1 - pi_obs))
                    
    test_statistic = -2 * log_lr_uc
    p_value = 1 - stats.chi2.cdf(test_statistic, df=1)
    return test_statistic, p_value

def christoffersen_independence(n00: int, n01: int, n10: int, n11: int) -> tuple:
    """
    Calculates the Christoffersen Independence test statistic based on Markov transitions.
    """
    n0 = n00 + n10
    n1 = n01 + n11
    pi_obs = n1 / (n0 + n1)
    
    pi_01 = n01 / (n00 + n01) if (n00 + n01) > 0 else 0
    pi_11 = n11 / (n10 + n11) if (n10 + n11) > 0 else 0
    
    # Numerator Log-Likelihood (assuming independence)
    ll_null = n1 * np.log(pi_obs) + n0 * np.log(1 - pi_obs)
    
    # Denominator Log-Likelihood (assuming Markov dependence)
    # Using np.log with a small floor to prevent log(0) errors
    ll_alt = 0
    if n00 > 0: ll_alt += n00 * np.log(1 - pi_01)
    if n01 > 0: ll_alt += n01 * np.log(pi_01)
    if n10 > 0: ll_alt += n10 * np.log(1 - pi_11)
    if n11 > 0: ll_alt += n11 * np.log(pi_11)
        
    test_statistic = -2 * (ll_null - ll_alt)
    p_value = 1 - stats.chi2.cdf(test_statistic, df=1)
    return test_statistic, p_value

# Example usage from text: 2000 observations, 33 exceedances, alpha = 0.01
# Transitions: n11=2, n00=1936, n01=31, n10=31
lr_uc_stat, lr_uc_p = kupiec_unconditional_coverage(2000, 33, 0.01)
lr_ind_stat, lr_ind_p = christoffersen_independence(1936, 31, 31, 2)
lr_cc_stat = lr_uc_stat + lr_ind_stat