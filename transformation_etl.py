import numpy as np
from scipy.stats import norm

def standard_normal_etl(alpha: float) -> float:
    """Calculates the Expected Tail Loss for a standard normal distribution."""
    z_alpha = norm.ppf(alpha)
    # PDF is symmetric, so pdf(Z_alpha) evaluates correctly
    return norm.pdf(z_alpha) / alpha

def calculate_johnson_su_etl(alpha: float, lam: float, gamma: float, delta: float, xi: float) -> float:
    """
    Calculates the analytic Expected Tail Loss under a fitted Johnson S_U distribution.
    (Equation IV.3.21)
    """
    sn_etl = standard_normal_etl(alpha)
    inner_term = (sn_etl - gamma) / delta
    
    etl_alpha = lam * np.sinh(inner_term) + xi
    return etl_alpha

def calculate_cornish_fisher_etl(alpha: float, mu: float, sigma: float, 
                                 skewness: float, excess_kurtosis: float) -> float:
    """
    Calculates the analytic Expected Tail Loss using the Cornish-Fisher Expansion.
    (Equation IV.3.22)
    """
    x = standard_normal_etl(alpha)
    
    # Polynomial transformation f(x) incorporating skew and kurtosis
    term_1 = x
    term_2 = (skewness / 6.0) * (x**2 - 1.0)
    term_3 = (excess_kurtosis / 24.0) * x * (x**2 - 3.0)
    term_4 = ((skewness**2) / 36.0) * x * (2.0 * x**2 - 5.0)
    
    f_x = term_1 + term_2 + term_3 - term_4
    
    # Scale transformation to empirical mean and volatility
    etl_alpha = (f_x * sigma) - mu
    
    return etl_alpha

# Setup for Example Cornish-Fisher ETL
conf_level = 0.01   # 1% Tail
mean_ret = 0.001    # 0.1% expected return
vol_ret = 0.015     # 1.5% volatility
skew = -1.4356      # Highly negatively skewed (e.g. iTraxx style)
exc_kurt = 4.93     # Heavy tailed

cf_etl = calculate_cornish_fisher_etl(
    alpha=conf_level, mu=mean_ret, sigma=vol_ret, 
    skewness=skew, excess_kurtosis=exc_kurt
)

print(f"Standard Normal 1% ETL (Base Multiple): {standard_normal_etl(conf_level):.4f}")
print(f"Cornish-Fisher 1% ETL (Loss Percentage): {cf_etl:.2%}")