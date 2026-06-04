import numpy as np
import scipy.stats as stats
import statsmodels.api as sm

def test_capm_joint_alphas(asset_excess_returns, market_excess_returns):
    """
    Performs a joint Chi-squared test to see if all alphas are zero.
    
    Parameters:
    asset_excess_returns (numpy.ndarray): T x n matrix of excess returns for n assets.
    market_excess_returns (numpy.ndarray): T x 1 vector of market excess returns.
    """
    T, n = asset_excess_returns.shape
    
    alphas = np.zeros(n)
    residuals = np.zeros((T, n))
    
    X = sm.add_constant(market_excess_returns)
    
    # Run OLS for each asset to extract alpha and residuals
    for i in range(n):
        model = sm.OLS(asset_excess_returns[:, i], X).fit()
        alphas[i] = model.params[0]
        residuals[:, i] = model.resid
        
    # Calculate the covariance matrix of the residuals (Sigma)
    Sigma = np.cov(residuals, rowvar=False)
    Sigma_inv = np.linalg.inv(Sigma)
    
    # Calculate market adjustment factor k_M
    mean_X = np.mean(market_excess_returns)
    std_X = np.std(market_excess_returns, ddof=1)
    k_M = 1.0 / (1.0 + (mean_X / std_X)**2)
    
    # Calculate the test statistic (W)
    alphas_vec = alphas.reshape(-1, 1)
    W_stat = k_M * (alphas_vec.T @ Sigma_inv @ alphas_vec).item()
    
    # Calculate the p-value from the Chi-squared distribution with n degrees of freedom
    p_value = stats.chi2.sf(W_stat, df=n)
    
    return W_stat, p_value, alphas

if __name__ == "__main__":
    np.random.seed(42)
    T, n = 60, 3  # 5 years of monthly data for 3 assets
    
    # Simulate market excess returns
    market_ex_ret = np.random.normal(0.005, 0.04, T)
    
    # Simulate asset excess returns (Asset 3 has a built-in alpha)
    asset_ex_ret = np.zeros((T, n))
    asset_ex_ret[:, 0] = 0.000 + 1.1 * market_ex_ret + np.random.normal(0, 0.02, T)
    asset_ex_ret[:, 1] = 0.000 + 0.9 * market_ex_ret + np.random.normal(0, 0.02, T)
    asset_ex_ret[:, 2] = 0.005 + 1.5 * market_ex_ret + np.random.normal(0, 0.02, T) # alpha = 0.5%
    
    W, p_val, estimated_alphas = test_capm_joint_alphas(asset_ex_ret, market_ex_ret)
    
    print("--- CAPM Joint Alpha Test ---")
    print(f"Estimated Alphas: {np.round(estimated_alphas, 4)}")
    print(f"Test Statistic (W): {W:.4f}")
    print(f"P-Value: {p_val:.4f}")
    if p_val < 0.05:
        print("Conclusion: Reject H0. The market is not in CAPM equilibrium (Alphas are non-zero).")
    else:
        print("Conclusion: Fail to reject H0. No evidence against CAPM equilibrium.")