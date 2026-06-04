import numpy as np

def lower_partial_moment(returns, threshold, alpha):
    """
    Calculates the Lower Partial Moment (LPM) of order alpha.
    """
    returns_array = np.array(returns)
    # max(0, tau - R)
    downside_deviations = np.maximum(0, threshold - returns_array)
    # E [ max(0, tau - R)^alpha ]
    lpm = np.mean(downside_deviations ** alpha)
    return lpm

def kappa_index(returns, threshold, alpha):
    """
    Calculates the Kappa index of order alpha.
    """
    expected_return = np.mean(returns)
    lpm = lower_partial_moment(returns, threshold, alpha)
    
    if lpm == 0:
        return np.inf if expected_return > threshold else 0.0
        
    return (expected_return - threshold) / (lpm ** (1.0 / alpha))

def omega_statistic(returns, threshold):
    """
    Calculates the Omega statistic (K_1 + 1).
    """
    k_1 = kappa_index(returns, threshold, alpha=1.0)
    return k_1 + 1.0

def sortino_ratio(returns, risk_free_rate):
    """
    Calculates the Sortino Ratio (Kappa index of order 2 with threshold = R_f).
    """
    return kappa_index(returns, risk_free_rate, alpha=2.0)

if __name__ == "__main__":
    # Synthetic periodic returns mimicking the text's active returns
    np.random.seed(42)
    # Generate some slightly skewed returns
    periodic_returns = np.random.normal(0.005, 0.04, 100) - np.random.exponential(0.005, 100)
    
    tau_benchmark = 0.00 # e.g., 0% benchmark return for the period
    tau_risk_free = 0.002 # e.g., 0.2% risk free rate per period
    
    # Calculate indices
    k1 = kappa_index(periodic_returns, tau_benchmark, alpha=1)
    k2 = kappa_index(periodic_returns, tau_benchmark, alpha=2)
    k3 = kappa_index(periodic_returns, tau_benchmark, alpha=3)
    
    omega = omega_statistic(periodic_returns, tau_benchmark)
    sortino = sortino_ratio(periodic_returns, tau_risk_free)
    
    print("--- Downside RAPMs (Periodic) ---")
    print(f"Kappa 1 (Threshold=Benchmark): {k1:.4f}")
    print(f"Kappa 2 (Threshold=Benchmark): {k2:.4f}")
    print(f"Kappa 3 (Threshold=Benchmark): {k3:.4f}")
    print(f"Omega Statistic (Threshold=Benchmark): {omega:.4f}")
    print(f"Sortino Ratio (Threshold=Risk-Free): {sortino:.4f}")
    # Note: Annualizing downside ratios properly requires scaling both the numerator
    # and the LPM denominator depending on the order alpha.