import numpy as np
import pandas as pd

def perform_pca(data_matrix, use_correlation=True):
    """
    Performs Principal Component Analysis on a T x n dataset.
    
    :param data_matrix: 2D array or DataFrame of T observations across n variables.
    :param use_correlation: If True, uses the correlation matrix. If False, uses covariance.
    :return: eigenvalues, eigenvectors, principal_components, variance_explained
    """
    # 1. Standardize/Center the data (X)
    X = np.array(data_matrix)
    X_centered = X - np.mean(X, axis=0)
    
    if use_correlation:
        # To use correlation matrix, we also normalize by standard deviation
        stdevs = np.std(X, axis=0)
        X_processed = X_centered / stdevs
        V = np.corrcoef(X.T)
    else:
        X_processed = X_centered
        V = np.cov(X.T)
        
    # 2. Compute Eigenvalues and Eigenvectors of V
    eigenvalues, W = np.linalg.eigh(V)
    
    # Sort them in descending order of eigenvalue magnitude
    sorted_indices = np.argsort(eigenvalues)[::-1]
    sorted_eigenvalues = eigenvalues[sorted_indices]
    sorted_W = W[:, sorted_indices]
    
    # 3. Calculate Principal Components: P = XW
    P = X_processed @ sorted_W
    
    # 4. Calculate proportion of variation explained
    total_variation = np.sum(sorted_eigenvalues)
    variance_explained = sorted_eigenvalues / total_variation
    cumulative_variance = np.cumsum(variance_explained)
    
    return sorted_eigenvalues, sorted_W, P, variance_explained, cumulative_variance

# --- Testing with the concepts from the Case Study ---
if __name__ == "__main__":
    # Hypothetical highly correlated system (similar to the European Equity Indices example)
    # 5 observations (T) across 3 indices (n)
    np.random.seed(42)
    base_trend = np.array([1, 2, 3, 4, 5])
    
    # Creating 3 highly correlated time series
    data = {
        'Index_1': base_trend + np.random.normal(0, 0.2, 5),
        'Index_2': base_trend * 1.1 + np.random.normal(0, 0.2, 5),
        'Index_3': base_trend * 0.9 + np.random.normal(0, 0.2, 5)
    }
    df = pd.DataFrame(data)
    
    print("--- PCA Analysis ---")
    eigenvals, W, components, var_exp, cum_var = perform_pca(df, use_correlation=True)
    
    print(f"Eigenvalues: {np.round(eigenvals, 4)}")
    print("\nProportion of Variation Explained:")
    for i, var in enumerate(var_exp):
        print(f"Principal Component {i+1}: {var:.2%}")
        
    print(f"\nCumulative Variation Explained: {np.round(cum_var * 100, 2)}")
    
    print("\nEigenvector Matrix (W) / Factor Loadings:")
    print(np.round(W, 4))