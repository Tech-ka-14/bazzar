import numpy as np
from scipy.stats import norm

def calculate_normal_benchmark_var(expected_active_return: float, tracking_error: float, 
                                   confidence_level: float, portfolio_value: float):
    """
    Calculates the Benchmark VaR assuming normally distributed active returns (Example IV.1.9).
    """
    alpha = 1.0 - confidence_level
    critical_value = norm.ppf(1 - alpha)
    
    bvar_pct = (critical_value * tracking_error) - expected_active_return
    return bvar_pct * portfolio_value

def calculate_historical_etl(returns: np.ndarray, confidence_level: float, portfolio_value: float):
    """
    Calculates the Historical VaR and Expected Tail Loss (ETL) from an empirical return series (Example IV.1.10).
    """
    alpha = 1.0 - confidence_level
    
    # Find the historical VaR threshold (alpha quantile)
    var_threshold = np.quantile(returns, alpha, method='lower')
    var_value = -var_threshold * portfolio_value
    
    # Filter for returns strictly worse than the VaR threshold
    tail_losses = returns[returns <= var_threshold]
    
    # ETL is the expected (average) value of these tail losses
    etl_value = -np.mean(tail_losses) * portfolio_value
    
    return var_value, etl_value

# 1. Example IV.1.9: Normal Benchmark VaR
exp_active_ret = 0.0
track_err = 0.03
conf = 0.99
port_val = 10_000_000

b_var = calculate_normal_benchmark_var(exp_active_ret, track_err, conf, port_val)
print(f"1% 1-Year Benchmark VaR (Normal): ${b_var:,.0f}")

# 2. Example IV.1.10: Historical ETL
# Mock dataset reflecting the 10 largest losses from Table IV.1.4 mixed with normal returns
mock_returns = np.random.normal(0.001, 0.01, 990)
tail_returns = np.array([-0.06127, -0.06033, -0.05690, -0.05233, -0.04241, 
                         -0.03891, -0.03864, -0.03801, -0.03727, -0.03549])
full_returns = np.concatenate([mock_returns, tail_returns])

hist_var, hist_etl = calculate_historical_etl(full_returns, 0.99, 1_007_580)
print(f"1% 1-Day Historical VaR: ${hist_var:,.0f}")
print(f"1% 1-Day Expected Tail Loss (ETL): ${hist_etl:,.0f}")