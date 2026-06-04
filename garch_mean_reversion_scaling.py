import numpy as np

def compare_garch_vs_sqrt_scaling(current_vol: float, long_run_vol: float, 
                                  alpha_garch: float, beta_garch: float, h_days: int):
    """
    Demonstrates the structural failure of the Square-Root rule under Mean-Reverting GARCH.
    Calculates the true integrated h-day variance under GARCH(1,1) vs naive scaling.
    """
    current_var = current_vol ** 2
    long_run_var = long_run_vol ** 2
    persistence = alpha_garch + beta_garch
    
    # 1. Naive Square Root Scaling (Assumes variance is constant at current_var)
    naive_h_day_variance = current_var * h_days
    
    # 2. True Integrated GARCH Variance over h days (accounting for mean reversion)
    # E[Var_t+k] = long_run_var + (persistence^k) * (current_var - long_run_var)
    true_h_day_variance = 0.0
    
    for k in range(1, h_days + 1):
        expected_daily_var = long_run_var + (persistence ** k) * (current_var - long_run_var)
        true_h_day_variance += expected_daily_var
        
    naive_h_day_vol = np.sqrt(naive_h_day_variance)
    true_h_day_vol = np.sqrt(true_h_day_variance)
    
    return naive_h_day_vol, true_h_day_vol

# Scenario 1: High Volatility Regime (Current Vol = 27.82%, Long Run Vol = 16.70%)
h = 10
naive_vol_high, true_vol_high = compare_garch_vs_sqrt_scaling(
    current_vol=0.2782, long_run_vol=0.1670, alpha_garch=0.08, beta_garch=0.90, h_days=h
)

# Scenario 2: Low Volatility Regime (Current Vol = 10.00%, Long Run Vol = 16.70%)
naive_vol_low, true_vol_low = compare_garch_vs_sqrt_scaling(
    current_vol=0.1000, long_run_vol=0.1670, alpha_garch=0.08, beta_garch=0.90, h_days=h
)

print("--- GARCH Mean Reversion vs. Square-Root Scaling ---")
print(f"Scenario 1: High Volatility (Current > Long Run)")
print(f"Naive Sqrt Volatility: {naive_vol_high:.2%}")
print(f"True GARCH Volatility: {true_vol_high:.2%} -> Naive rule OVERESTIMATED risk by ignoring downward mean reversion.\n")

print(f"Scenario 2: Low Volatility (Current < Long Run)")
print(f"Naive Sqrt Volatility: {naive_vol_low:.2%}")
print(f"True GARCH Volatility: {true_vol_low:.2%} -> Naive rule UNDERESTIMATED risk by ignoring upward mean reversion.")