import numpy as np

def autocorrelation_annualization_factor(h, rho):
    """
    Calculates the adjusted annualization factor for standard deviation 
    when returns have first-order autocorrelation (rho).
    """
    if rho == 0:
        return np.sqrt(h)
    
    term1 = h
    term2 = (2 * rho) / ((1 - rho)**2)
    term3 = ((h - 1) * (1 - rho)) - (rho * (1 - rho**(h - 1)))
    
    return np.sqrt(term1 + term2 * term3)

def adjusted_sharpe_ratio_higher_moments(sharpe_ratio, skewness, excess_kurtosis):
    """
    Calculates the Adjusted Sharpe Ratio (ASR2) incorporating skewness and kurtosis.
    """
    sr = sharpe_ratio
    term_skew = (skewness / 6.0) * (sr**2)
    term_kurt = (excess_kurtosis / 24.0) * (sr**3)
    return sr + term_skew - term_kurt

def generalized_sharpe_ratio(sharpe_ratio, skewness, excess_kurtosis):
    """
    Calculates the Generalized Sharpe Ratio (GSR) based on expected utility.
    """
    sr = sharpe_ratio
    term_skew = (skewness / 3.0) * (sr**3)
    term_kurt = (excess_kurtosis / 12.0) * (sr**4)
    
    inside_sqrt = (sr**2) + term_skew - term_kurt
    return np.sqrt(max(0, inside_sqrt)) # Ensure non-negative before sqrt

if __name__ == "__main__":
    # --- Example I.6.12 & I.6.13 Implementation ---
    h = 250 # Daily returns
    rho = 0.20 # Autocorrelation
    
    # 1. Autocorrelation adjustment
    standard_factor = np.sqrt(h)
    adjusted_factor = autocorrelation_annualization_factor(h, rho)
    print("--- Autocorrelation Adjustment ---")
    print(f"Standard sqrt(h) factor: {standard_factor:.2f}")
    print(f"Autocorrelation Adjusted factor: {adjusted_factor:.2f}")
    
    # 2. Higher Moments Adjustment (Fund data from Example I.6.13)
    sr_autocorr_adj = 0.3984 # ASR1
    skew = -0.742
    kurt = 1.808
    
    asr2 = adjusted_sharpe_ratio_higher_moments(sr_autocorr_adj, skew, kurt)
    gsr = generalized_sharpe_ratio(sr_autocorr_adj, skew, kurt)
    
    print("\n--- Higher Moment Adjustments ---")
    print(f"Base Sharpe (ASR1): {sr_autocorr_adj:.4f}")
    print(f"Adjusted Sharpe (ASR2): {asr2:.4f}")
    print(f"Generalized Sharpe (GSR): {gsr:.4f}")