import numpy as np

def calculate_adjusted_time_horizon(h: int, rho: float) -> float:
    """
    Analytically calculates the adjusted time horizon (h_tilde) for a first-order 
    autoregressive (AR1) return process using Equation IV.2.10.
    """
    if rho == 0:
        return float(h)
    
    term_1 = (h - 1) * (1 - rho)
    term_2 = rho * (1 - rho**(h - 1))
    
    adjustment_factor = 2 * (rho / (1 - rho)**2) * (term_1 - term_2)
    h_tilde = h + adjustment_factor
    
    return h_tilde

def scale_volatility(daily_vol: float, h_days: int, rho: float = 0.0) -> float:
    """
    Scales daily volatility to an h-day horizon, accounting for serial correlation.
    """
    h_tilde = calculate_adjusted_time_horizon(h_days, rho)
    return daily_vol * np.sqrt(h_tilde)

# Example IV.2.12: iTraxx Europe 5-Year Index (Table IV.2.37)
daily_vol_bp = 2.4037
autocorrelation = 0.1079
trading_days_per_year = 250

# 1. Base i.i.d. Volatility
annual_vol_iid = scale_volatility(daily_vol_bp, trading_days_per_year, rho=0.0)

# 2. Autocorrelation-Adjusted Volatility
annual_vol_adj = scale_volatility(daily_vol_bp, trading_days_per_year, rho=autocorrelation)
adjusted_h = calculate_adjusted_time_horizon(trading_days_per_year, autocorrelation)

print("--- iTraxx Europe 5-Year Index Volatility ---")
print(f"Daily Volatility: {daily_vol_bp} basis points")
print(f"Autocorrelation: {autocorrelation}\n")

print(f"I.I.D. Annual Volatility: {annual_vol_iid:.1f} basis points (h = 250)")
print(f"Autocorrelated Annual Volatility: {annual_vol_adj:.1f} basis points (h_tilde = {adjusted_h:.0f})")