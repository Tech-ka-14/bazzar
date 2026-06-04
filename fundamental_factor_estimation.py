import numpy as np
import statsmodels.api as sm

def estimate_fundamental_factors(asset_returns, fundamental_factors):
    """
    Estimates the sensitivities (betas) of an asset to various fundamental risk factors.
    
    Parameters:
    asset_returns (numpy.ndarray): 1D array of the asset's log returns.
    fundamental_factors (numpy.ndarray): 2D array (T x k) of the fundamental factor returns 
                                         (e.g., Market, Industry, Growth, Cap).
    
    Returns:
    dict: A dictionary containing the estimated Alpha, Betas, and R-squared.
    """
    # Add a constant term to estimate the Alpha
    X = sm.add_constant(fundamental_factors)
    
    # Fit the OLS model
    model = sm.OLS(asset_returns, X).fit()
    
    # Extract Alpha and Betas
    alpha = model.params[0]
    betas = model.params[1:]
    
    return {
        "alpha": float(alpha),
        "betas": betas.flatten(),
        "r_squared": float(model.rsquared),
        "specific_risk": float(np.std(model.resid, ddof=1)) # Idiosyncratic volatility
    }

if __name__ == "__main__":
    # --- Example Implementation ---
    # Simulating the Case Study setup: 100 periods of returns
    np.random.seed(42)
    T = 100
    
    # 4 Fundamental Factors: Market, Communications (Industry), Growth, Large Cap
    market = np.random.normal(0.005, 0.04, T)
    industry = np.random.normal(0.002, 0.03, T)
    growth = np.random.normal(0.001, 0.02, T)
    large_cap = np.random.normal(0.0015, 0.015, T)
    
    factors = np.column_stack((market, industry, growth, large_cap))
    
    # Simulate an asset (e.g., Vodafone) with specific sensitivities to these factors
    # True betas: Market=1.1, Industry=0.8, Growth=0.2, Cap=0.5
    asset = 0.001 + 1.1*market + 0.8*industry + 0.2*growth + 0.5*large_cap + np.random.normal(0, 0.01, T)
    
    results = estimate_fundamental_factors(asset, factors)
    
    print("--- Fundamental Factor Sensitivities ---")
    print(f"Alpha:         {results['alpha']:.6f}")
    print(f"Market Beta:   {results['betas'][0]:.4f}")
    print(f"Industry Beta: {results['betas'][1]:.4f}")
    print(f"Growth Beta:   {results['betas'][2]:.4f}")
    print(f"Cap Beta:      {results['betas'][3]:.4f}")
    print(f"Model R^2:     {results['r_squared']:.4f}")