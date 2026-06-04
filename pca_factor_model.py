import numpy as np

def perform_pca(returns_matrix, use_correlation=False):
    """
    Performs Principal Component Analysis (PCA) on a matrix of asset returns
    to extract statistical risk factors.
    
    Parameters:
    returns_matrix (numpy.ndarray): T x m matrix of historical returns 
                                    (T observations, m assets).
    use_correlation (bool): If True, performs PCA on the correlation matrix 
                            instead of the covariance matrix.
    
    Returns:
    dict: A dictionary containing the Eigenvalues, Eigenvectors, Principal 
          Components (Scores), and the Explained Variance Ratio.
    """
    # 1. Center the returns (subtract the mean of each asset's return)
    mean_returns = np.mean(returns_matrix, axis=0)
    centered_returns = returns_matrix - mean_returns
    
    # 2. Compute the Covariance or Correlation Matrix
    if use_correlation:
        # rowvar=False means each column is a variable
        dispersion_matrix = np.corrcoef(centered_returns, rowvar=False) 
    else:
        dispersion_matrix = np.cov(centered_returns, rowvar=False)
        
    # 3. Calculate Eigenvalues and Eigenvectors
    # eigh is highly optimized for symmetric matrices like covariance/correlation matrices
    eigenvalues, eigenvectors = np.linalg.eigh(dispersion_matrix)
    
    # 4. Sort in descending order (largest eigenvalue first)
    sorted_indices = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[sorted_indices]
    eigenvectors = eigenvectors[:, sorted_indices]
    
    # 5. Calculate the Principal Components (Statistical Risk Factors)
    # P = X * W
    principal_components = centered_returns @ eigenvectors
    
    # 6. Calculate Explained Variance (Percentage of total risk captured by each factor)
    total_variance = np.sum(eigenvalues)
    explained_variance_ratio = eigenvalues / total_variance
    
    return {
        "eigenvalues": eigenvalues,
        "eigenvectors": eigenvectors,
        "principal_components": principal_components,
        "explained_variance_ratio": explained_variance_ratio
    }

if __name__ == "__main__":
    # --- Example Application ---
    # Simulate T=250 days of returns for m=3 highly correlated assets
    np.random.seed(42)
    T = 250
    
    # Simulate a common market factor
    market_factor = np.random.normal(0, 0.015, T)
    
    # Simulate 3 assets driven largely by the market factor + specific noise
    asset_1 = 1.1 * market_factor + np.random.normal(0, 0.005, T)
    asset_2 = 0.9 * market_factor + np.random.normal(0, 0.006, T)
    asset_3 = 1.3 * market_factor + np.random.normal(0, 0.004, T)
    
    portfolio_returns = np.column_stack((asset_1, asset_2, asset_3))
    
    # Perform PCA using the Covariance Matrix
    pca_results = perform_pca(portfolio_returns, use_correlation=False)
    
    print("--- Principal Component Analysis (PCA) ---")
    print("\nExplained Variance Ratio by Component:")
    for i, var in enumerate(pca_results["explained_variance_ratio"]):
        print(f"Principal Component {i+1}: {var * 100:.2f}% of total risk")
        
    print("\nEigenvector for Principal Component 1 (Factor Loadings):")
    print(np.round(pca_results["eigenvectors"][:, 0], 4))