import numpy as np

def orthogonal_ewma_covariance(returns_matrix, k_components=3, lambdas=None):
    """
    Constructs a positive semi-definite covariance matrix using the Orthogonal EWMA (O-EWMA) approach.
    
    Parameters:
    returns_matrix : 2D numpy array (T observations x M assets)
    k_components   : Number of principal components to retain
    lambdas        : List of specific smoothing constants for each principal component
    """
    T, M = returns_matrix.shape
    if lambdas is None:
        lambdas = [0.94] * k_components  # Default if not specified

    # 1. Compute the equally weighted covariance matrix and its eigendecomposition
    eq_cov_matrix = np.cov(returns_matrix, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(eq_cov_matrix)
    
    # Sort descending
    idx = np.argsort(eigenvalues)[::-1]
    eigenvectors = eigenvectors[:, idx]
    
    # 2. Extract the first k principal components (W matrix)
    W_k = eigenvectors[:, :k_components]
    
    # 3. Calculate the Principal Component scores
    # Center the returns
    centered_returns = returns_matrix - np.mean(returns_matrix, axis=0)
    pc_scores = np.dot(centered_returns, W_k)
    
    # 4. Apply EWMA to the variances of the retained Principal Components
    ewma_pc_variances = np.zeros(k_components)
    
    for i in range(k_components):
        lmbda = lambdas[i]
        var_t = np.var(pc_scores[:, i]) # initialize
        
        # Run recursive EWMA on this specific principal component
        for t in range(1, T):
            var_t = (1 - lmbda) * (pc_scores[t-1, i]**2) + lmbda * var_t
            
        ewma_pc_variances[i] = var_t
        
    # 5. Reconstruct the final positive semi-definite Covariance Matrix
    # V = W_k * Diagonal(EWMA_PC_Variances) * W_k.T
    diagonal_pc_matrix = np.diag(ewma_pc_variances)
    o_ewma_matrix = np.dot(np.dot(W_k, diagonal_pc_matrix), W_k.T)
    
    return o_ewma_matrix