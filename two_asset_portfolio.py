import numpy as np

def portfolio_variance_2_assets(w, vol1, vol2, rho):
    """
    Calculates the variance of a 2-asset portfolio.
    """
    variance = (w**2 * vol1**2) + \
               ((1 - w)**2 * vol2**2) + \
               (2 * rho * w * (1 - w) * vol1 * vol2)
    return variance

def min_variance_weight_2_assets(vol1, vol2, rho):
    """
    Calculates the optimal weight (w*) for Asset 1 that minimizes portfolio variance.
    """
    numerator = vol2**2 - (rho * vol1 * vol2)
    denominator = vol1**2 + vol2**2 - (2 * rho * vol1 * vol2)
    
    # Handle the edge case of perfectly correlated identical assets
    if denominator == 0:
        return 0.5 
        
    return numerator / denominator

if __name__ == "__main__":
    # --- Example I.6.5 Implementation --- 
    v1 = 0.20 # Asset 1 Volatility = 20%
    v2 = 0.30 # Asset 2 Volatility = 30%
    correlation = -0.25
    
    # Calculate Optimal Weight
    opt_w1 = min_variance_weight_2_assets(v1, v2, correlation)
    opt_w2 = 1 - opt_w1
    
    # Calculate Minimum Volatility
    min_var = portfolio_variance_2_assets(opt_w1, v1, v2, correlation)
    min_vol = np.sqrt(min_var)
    
    print("--- 2-Asset Minimum Variance Portfolio ---")
    print(f"Optimal Weight Asset 1: {opt_w1 * 100:.2f}%")
    print(f"Optimal Weight Asset 2: {opt_w2 * 100:.2f}%")
    print(f"Minimum Portfolio Volatility: {min_vol * 100:.2f}%")