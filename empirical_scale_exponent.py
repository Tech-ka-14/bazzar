import numpy as np
import statsmodels.api as sm

def estimate_scale_exponent(h_days_array: np.ndarray, quantiles_h_array: np.ndarray, quantile_1d: float) -> float:
    """
    Estimates the empirical Power Law Scale Exponent (1/xi) using a log-log regression.
    Equation IV.3.2.
    
    Parameters:
    h_days_array (np.ndarray): Array of risk horizons (e.g., [2, 5, 10, 20]).
    quantiles_h_array (np.ndarray): The measured empirical quantiles for each horizon.
    quantile_1d (float): The base 1-day empirical quantile.
    
    Returns:
    float: The estimated scale exponent (1/xi). 
           (0.5 indicates Normal/Square-root scaling. >0.5 indicates trending/fat-tails).
    """
    # Calculate the Y-axis: ln(x_h) - ln(x_1)
    y_log_ratio = np.log(np.abs(quantiles_h_array)) - np.log(np.abs(quantile_1d))
    
    # Calculate the X-axis: ln(h)
    x_log_h = np.log(h_days_array)
    
    # We force the regression through the origin (no intercept) because when h=1, ln(h)=0 and ratio=0.
    model = sm.OLS(y_log_ratio, x_log_h)
    results = model.fit()
    
    # The slope is the scale exponent (1/xi)
    scale_exponent = results.params[0]
    
    return scale_exponent

# --- Example IV.3.2.4: Scale Exponents for S&P 500 ---
# Mock data representing empirical measurements of the 5% Quantile over various horizons
h_horizons = np.array([2, 5, 10, 20])
var_1d = 0.0150 # 1.50% Base 1-day VaR

# Measured multi-day VaRs (simulated to reflect a scale exponent of approx ~0.45)
vars_h = np.array([0.0205, 0.0310, 0.0425, 0.0580]) 

empirical_exponent = estimate_scale_exponent(h_horizons, vars_h, var_1d)

print(f"Empirical Scale Exponent (1/xi): {empirical_exponent:.4f}")
if empirical_exponent < 0.5:
    print("Interpretation: Risk scales slower than the square root of time (Mean-Reverting / Anti-persistent).")
elif empirical_exponent > 0.5:
    print("Interpretation: Risk scales faster than the square root of time (Trending / Persistent).")