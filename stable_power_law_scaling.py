def scale_historical_var(var_1_day: float, h_days: int, scale_exponent: float) -> float:
    """
    Scales a 1-day Historical VaR to an h-day VaR using a generalized power law.
    
    Parameters:
    var_1_day (float): The base 1-day VaR estimate.
    h_days (int): The target risk horizon in days.
    scale_exponent (float): The stability index/power scaling factor 'c'.
                            (0.5 = Normal/Square Root Rule. >0.5 = Heavy Tailed)
    """
    scaling_factor = h_days ** scale_exponent
    return var_1_day * scaling_factor

# --- Conceptual Demonstration ---
base_1d_var = 0.015  # 1.5% 1-day VaR
target_horizon = 10  # 10-day Risk Horizon

# 1. Using the naive "Square Root of Time" Rule (c = 0.5)
var_10d_naive = scale_historical_var(base_1d_var, target_horizon, scale_exponent=0.5)

# 2. Using a customized Power Law for a heavy-tailed stable distribution (e.g., c = 0.6)
var_10d_heavy = scale_historical_var(base_1d_var, target_horizon, scale_exponent=0.6)

print(f"Base 1-Day VaR: {base_1d_var:.2%}")
print(f"10-Day VaR (Naive Square Root Rule): {var_10d_naive:.2%}")
print(f"10-Day VaR (Empirical Power Law c=0.6): {var_10d_heavy:.2%}")
print(f"Difference in risk estimate: {var_10d_heavy - var_10d_naive:.2%} (The naive rule severely understates the scaled risk)")