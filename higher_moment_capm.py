import numpy as np

def calculate_higher_moment_betas(asset_returns, market_returns):
    """
    Calculates the Beta (Covariance), Coskewness, and Cokurtosis of an asset
    relative to the market portfolio.
    """
    # Calculate mean-deviated returns
    asset_tilde = asset_returns - np.mean(asset_returns)
    market_tilde = market_returns - np.mean(market_returns)
    
    # Calculate Expected Values (using sample means as estimators)
    E_R_i_R_M = np.mean(asset_tilde * market_tilde)
    E_R_M_2 = np.mean(market_tilde ** 2)
    
    E_R_i_R_M_2 = np.mean(asset_tilde * (market_tilde ** 2))
    E_R_M_3 = np.mean(market_tilde ** 3)
    
    E_R_i_R_M_3 = np.mean(asset_tilde * (market_tilde ** 3))
    E_R_M_4 = np.mean(market_tilde ** 4)
    
    # Calculate the risk parameters (Equation I.6.55)
    beta_cov = E_R_i_R_M / E_R_M_2
    
    # Protect against division by zero if market is perfectly symmetrical (skewness = 0)
    gamma_coskew = E_R_i_R_M_2 / E_R_M_3 if E_R_M_3 != 0 else 0 
    
    eta_cokurt = E_R_i_R_M_3 / E_R_M_4 if E_R_M_4 != 0 else 0
    
    return beta_cov, gamma_coskew, eta_cokurt

if __name__ == "__main__":
    np.random.seed(42)
    
    # Simulate non-normal market returns (e.g., negative skew, fat tails)
    T = 1000
    market_ret = np.random.standard_t(df=4, size=T) * 0.02 + 0.005 
    
    # Simulate an asset that is highly sensitive to market crashes (Coskewness)
    asset_ret = 1.2 * market_ret + (market_ret**2 * -0.5) + np.random.normal(0, 0.01, T)
    
    beta, coskew, cokurt = calculate_higher_moment_betas(asset_ret, market_ret)
    
    print("--- Higher Moment CAPM Risk Metrics ---")
    print(f"Standard Beta (Covariance): {beta:.4f}")
    print(f"Coskewness (Systematic Skewness): {coskew:.4f}")
    print(f"Cokurtosis (Systematic Kurtosis): {cokurt:.4f}")