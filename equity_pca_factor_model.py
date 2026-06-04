import numpy as np
import statsmodels.api as sm

def build_equity_pca_model(returns_matrix, k_components):
    """
    Builds a statistical factor model using PCA on equity returns and OLS regression.
    
    Parameters:
    returns_matrix (numpy.ndarray): T x n matrix of historical stock returns.
    k_components (int): The number of principal components to retain (k).
    
    Returns:
    dict: A dictionary containing the extracted factors, alphas, factor loadings (betas), 
          specific variances, and R-squared values for each stock.
    """
    T, n = returns_matrix.shape
    
    # --- STEP 1: Principal Component Analysis ---
    # Center the returns
    mean_returns = np.mean(returns_matrix, axis=0)
    centered_returns = returns_matrix - mean_returns
    
    # Calculate Covariance Matrix
    cov_matrix = np.cov(centered_returns, rowvar=False)
    
    # Extract Eigenvalues and Eigenvectors
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
    
    # Sort in descending order
    idx = np.argsort(eigenvalues)[::-1]
    eigenvectors = eigenvectors[:, idx]
    
    # Calculate the principal component scores (P = X * W)
    all_components = centered_returns @ eigenvectors
    
    # Retain only the first k components (These are our statistical risk factors)
    P_k = all_components[:, :k_components]
    
    # --- STEP 2: Linear Regression for each stock ---
    alphas = np.zeros(n)
    betas = np.zeros((n, k_components))
    specific_variances = np.zeros(n)
    r_squared_vals = np.zeros(n)
    
    # Add a constant term to the factors to estimate the regression Alpha
    X_reg = sm.add_constant(P_k)
    
    for j in range(n):
        # Regress the j-th stock's returns against the k statistical factors
        model = sm.OLS(returns_matrix[:, j], X_reg).fit()
        
        alphas[j] = model.params[0]
        betas[j, :] = model.params[1:]
        
        # Specific risk is the variance of the regression residuals
        specific_variances[j] = np.var(model.resid, ddof=1)
        r_squared_vals[j] = model.rsquared
        
    return {
        "statistical_factors": P_k,
        "alphas": alphas,
        "betas": betas,
        "specific_variances": specific_variances,
        "r_squared": r_squared_vals
    }

if __name__ == "__main__":
    # --- Example Application ---
    # Simulate T=250 days of returns for n=5 stocks
    np.random.seed(42)
    T, n = 250, 5
    
    # Generate some correlated random data to represent stock returns
    base_market = np.random.normal(0, 0.012, T)
    base_sector = np.random.normal(0, 0.008, T)
    
    simulated_returns = np.zeros((T, n))
    for i in range(n):
        # Create returns heavily driven by the base factors plus some specific noise
        simulated_returns[:, i] = (np.random.uniform(0.5, 1.5) * base_market + 
                                   np.random.uniform(-1, 1) * base_sector + 
                                   np.random.normal(0, 0.005, T))
        
    # Build the PCA factor model retaining the top k=2 components
    k = 2
    model_results = build_equity_pca_model(simulated_returns, k_components=k)
    
    print(f"--- Equity PCA Factor Model (Retaining {k} Components) ---")
    for j in range(n):
        print(f"\nStock {j+1}:")
        print(f"  Alpha:              {model_results['alphas'][j]:.6f}")
        print(f"  Beta to Factor 1:   {model_results['betas'][j, 0]:.4f}")
        print(f"  Beta to Factor 2:   {model_results['betas'][j, 1]:.4f}")
        print(f"  Specific Variance:  {model_results['specific_variances'][j]:.6f}")
        print(f"  Model R-Squared:    {model_results['r_squared'][j]:.4f}")