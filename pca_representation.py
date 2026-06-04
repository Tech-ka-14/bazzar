import numpy as np

def reconstruct_from_pca(principal_components, eigenvectors, num_components):
    """
    Approximates the original standardized variables (e.g., interest rate changes) 
    using a truncated set of principal components.
    
    Parameters:
    principal_components (numpy.ndarray): T x n matrix of all principal component scores.
    eigenvectors (numpy.ndarray): n x n matrix of eigenvectors (factor weights).
    num_components (int): The number of components to keep (k).
    
    Returns:
    numpy.ndarray: T x n matrix of the approximated original variables.
    """
    # Truncate the components and the eigenvectors to the first 'k' dimensions
    p_k = principal_components[:, :num_components]
    w_k = eigenvectors[:, :num_components]
    
    # Reconstruct the original variables: X_approx = P_k * W_k^T
    # Note: Since the text defines it as weights * components for a single row, 
    # the matrix equivalent for the full dataset is P_k @ W_k.T
    approximated_variables = p_k @ w_k.T
    
    return approximated_variables

if __name__ == "__main__":
    # --- Example Application (Replicating Eq II.2.6 structure) ---
    T = 5 # 5 days of data
    n = 50 # 50 yield curve rates
    k = 3 # Keeping only Shift, Tilt, and Convexity components
    
    # Synthetic principal component scores (T x k)
    p_k_simulated = np.random.normal(0, 1, (T, k))
    
    # Synthetic first 3 eigenvectors for 50 rates (n x k)
    w_k_simulated = np.random.uniform(-0.2, 0.7, (n, k))
    
    # Reconstruct the 50 rates over 5 days using only the 3 components
    reconstructed_rates = p_k_simulated @ w_k_simulated.T
    
    print("--- PCA Dimensionality Reduction ---")
    print(f"Original shape required: {T} days x {n} rates")
    print(f"Approximated using: {T} days of {k} components")
    print(f"Shape of reconstructed data: {reconstructed_rates.shape}")