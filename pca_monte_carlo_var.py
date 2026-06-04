import numpy as np

def simulate_pca_factors(eigenvalues: np.ndarray, n_simulations: int, distribution: str = 'normal', df: int = None) -> np.ndarray:
    """
    Simulates orthogonal Principal Component risk factors directly from eigenvalues.
    """
    k = len(eigenvalues)
    
    # The Cholesky matrix of orthogonal components is just the square root of the eigenvalues
    pca_vols = np.sqrt(eigenvalues)
    
    if distribution == 'normal':
        z = np.random.standard_normal((n_simulations, k))
    elif distribution == 'student_t' and df is not None:
        u = np.random.uniform(0, 1, (n_simulations, k))
        standard_t = stats.t.ppf(u, df=df)
        z = standard_t * np.sqrt((df - 2) / df)
    else:
        raise ValueError("Invalid distribution type")
        
    # Scale the independent draws by the PCA volatilities
    pca_simulations = z * pca_vols
    return pca_simulations