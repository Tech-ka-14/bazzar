import numpy as np


def construct_statistical_factor_model(returns_matrix, k):
    """
    Constructs a statistical factor model by extracting the first k principal
    components from a matrix of asset returns.

    Parameters:
    returns_matrix (numpy.ndarray): T x n matrix of asset returns (T periods, n assets).
    k (int): Number of principal components (factors) to extract.

    Returns:
    tuple: (factors, betas, r_squared)
           factors: T x k matrix of principal component returns.
           betas: k x n matrix of factor sensitivities.
           r_squared: Array of R^2 values for each asset's regression on the factors.
    """
    T, n = returns_matrix.shape

    # 1. Center the returns
    mean_returns = np.mean(returns_matrix, axis=0)
    centered_returns = returns_matrix - mean_returns

    # 2. Compute the covariance matrix (n x n)
    cov_matrix = np.cov(centered_returns, rowvar=False)

    # 3. Eigen-decomposition
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)

    # Sort eigenvalues and eigenvectors in descending order
    sorted_indices = np.argsort(eigenvalues)[::-1]
    sorted_eigenvectors = eigenvectors[:, sorted_indices]

    # 4. Extract the first k principal components as our factors (T x k)
    W_k = sorted_eigenvectors[:, :k]
    factors = centered_returns @ W_k

    # 5. Run OLS for each asset against the k factors to find Betas
    # Y = XB + E  =>  B = (X'X)^-1 X'Y
    # Here X is the factors matrix (T x k), Y is the centered returns (T x n)
    X = np.column_stack((np.ones(T), factors))  # Add intercept

    betas = []
    r_squared = []

    for i in range(n):
        y = centered_returns[:, i]

        # OLS
        B = np.linalg.inv(X.T @ X) @ X.T @ y
        betas.append(B[1:])  # Exclude intercept

        # Calculate R^2
        y_pred = X @ B
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared.append(1 - (ss_res / ss_tot))

    return factors, np.array(betas).T, np.array(r_squared)


if __name__ == "__main__":
    # --- Example Application ---
    # Simulate T=250 days of returns for n=10 stocks driven by 2 underlying factors
    np.random.seed(42)
    T, n = 250, 10

    # Two underlying true factors
    f1 = np.random.normal(0, 0.02, T)
    f2 = np.random.normal(0, 0.01, T)

    # Simulate asset returns with different sensitivities to f1 and f2, plus noise
    returns = np.zeros((T, n))
    for i in range(n):
        beta1 = np.random.uniform(0.5, 1.5)
        beta2 = np.random.uniform(-0.5, 0.5)
        noise = np.random.normal(0, 0.005, T)
        returns[:, i] = beta1 * f1 + beta2 * f2 + noise

    # Construct the factor model with k=2
    k = 2
    factors, betas, r2 = construct_statistical_factor_model(returns, k)

    print("--- Statistical Factor Model (PCA) ---")
    print(f"Shape of Extracted Factors: {factors.shape}")
    print(f"Shape of Beta Matrix: {betas.shape}")
    print("R-squared for each asset:")
    print(np.round(r2, 4))
