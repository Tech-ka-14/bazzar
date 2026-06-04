import numpy as np
from scipy.stats import norm

def calculate_quanto_var_components(equity_beta: float, vol_equity: float, vol_fx: float, 
                                    quanto_corr: float, portfolio_val: float, 
                                    horizon_days: int = 10, alpha: float = 0.01):
    """
    Calculates the Total Systematic, Stand-alone Equity, and Stand-alone FX VaR 
    incorporating the quanto correlation (Equations IV.2.49 to IV.2.52).
    """
    # Scale annual volatilities to the specific horizon
    time_scale = np.sqrt(horizon_days / 250.0)
    vol_eq_h = vol_equity * time_scale
    vol_fx_h = vol_fx * time_scale
    
    # Calculate Total Portfolio Volatility (Eq IV.2.49)
    variance_h = (equity_beta**2 * vol_eq_h**2) + (vol_fx_h**2) + \
                 (2 * equity_beta * quanto_corr * vol_eq_h * vol_fx_h)
    vol_total_h = np.sqrt(variance_h)
    
    # Calculate VaRs
    z_score = norm.ppf(1 - alpha)
    
    total_var = z_score * vol_total_h * portfolio_val
    equity_var = z_score * (equity_beta * vol_eq_h) * portfolio_val
    fx_var = z_score * vol_fx_h * portfolio_val
    
    return total_var, equity_var, fx_var

# Example IV.2.14: Equity and Forex VaR
portfolio_usd = 2_000_000
beta_uk = 1.5
vol_ftse = 0.15
vol_gbpusd = 0.20
correlation = 0.30

total, eq_var, fx_var = calculate_quanto_var_components(
    beta_uk, vol_ftse, vol_gbpusd, correlation, portfolio_usd, horizon_days=10
)

print(f"Stand-alone Equity VaR: ${eq_var:,.0f}")
print(f"Stand-alone Forex VaR: ${fx_var:,.0f}")
print(f"Sum of Stand-alone VaRs: ${eq_var + fx_var:,.0f}")
print("-" * 35)
print(f"Total Systematic VaR (Diversified): ${total:,.0f}")