import numpy as np
from scipy.stats import norm

def calculate_pc_var(theta: np.ndarray, covariance_matrix: np.ndarray, 
                     num_components: int, alpha: float = 0.01):
    """
    Calculates the Principal Component Value at Risk (PC VaR) by reducing 
    the dimensionality of the yield curve risk factors.
    
    Parameters:
    theta (np.ndarray): The original PV01 sensitivity vector (n x 1).
    covariance_matrix (np.ndarray): The original risk factor covariance matrix (n x n).
    num_components (int): The number of principal components to retain (p).
    alpha (float): The significance level for VaR.
    
    Returns:
    tuple: (PC VaR, Percentage of Variance Explained)
    """
    # 1. Perform Eigen-decomposition on the Covariance Matrix
    eigenvalues, eigenvectors = np.linalg.eigh(covariance_matrix)
    
    # Sort eigenvalues and eigenvectors in descending order (largest first)
    sorted_indices = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[sorted_indices]
    eigenvectors = eigenvectors[:, sorted_indices]
    
    # Calculate how much total variance is explained by the retained components
    total_variance = np.sum(eigenvalues)
    explained_variance = np.sum(eigenvalues[:num_components]) / total_variance
    
    # 2. Truncate matrices to the chosen number of principal components (p)
    lambda_p = np.diag(eigenvalues[:num_components]) # p x p diagonal matrix
    w_p = eigenvectors[:, :num_components]           # n x p matrix
    
    # 3. Map original PV01s to Principal Component Sensitivities (Eq: theta_p = W_p' * theta)
    theta_p = w_p.T @ theta
    
    # 4. Calculate Portfolio Variance using PC sensitivities and Eigenvalues
    portfolio_variance = theta_p.T @ lambda_p @ theta_p
    
    # 5. Calculate PC VaR
    critical_value = norm.ppf(1 - alpha)
    pc_var = critical_value * np.sqrt(portfolio_variance)
    
    return pc_var, explained_variance

# --- Example based on the 60-Month UK Fixed Income Portfolio Case Study ---
# We simulate a 60-vertex scenario based on Figure IV.2.2

num_vertices = 60
np.random.seed(42) # Seed for reproducibility

# 1. Recreate a slice of the PV01 vector from Figure IV.2.2 (first 10 months for brevity + zeros)
# In reality, this would be the exact 60-item array from the table
theta_60m = np.zeros(num_vertices)
sample_pv01s = [0.6, 0.3, 0.2, -1.6, -0.7, -1.8, 0.7, -3.0, -0.1, 0.3] 
theta_60m[:len(sample_pv01s)] = sample_pv01s
# Converting £000s to raw pounds
theta_60m = theta_60m * 1000 

# 2. Create a mock highly-collinear 60x60 covariance matrix (typical of yield curves)
# Generating a correlation matrix where close maturities are highly correlated
base_vol = 50 # basis points
corr_matrix = np.zeros((num_vertices, num_vertices))
for i in range(num_vertices):
    for j in range(num_vertices):
        # Correlation decays exponentially based on distance between maturities
        corr_matrix[i, j] = np.exp(-0.05 * abs(i - j)) 

# Convert correlation to covariance
vols = np.full(num_vertices, base_vol)
cov_matrix_60m = np.outer(vols, vols) * corr_matrix

# 3. Calculate PC VaR retaining only the first 3 Principal Components 
# (Level, Steepness, Curvature)
n_pcs = 3
confidence = 0.01 # 1% VaR

pc_var_estimate, var_explained = calculate_pc_var(
    theta=theta_60m, 
    covariance_matrix=cov_matrix_60m, 
    num_components=n_pcs, 
    alpha=confidence
)

print("--- Principal Component VaR Analysis ---")
print(f"Original Dimensions: {num_vertices} Risk Factors")
print(f"Reduced Dimensions: {n_pcs} Principal Components")
print(f"Total System Variance Captured: {var_explained:.2%}")
print(f"1% PC VaR Estimate: £{pc_var_estimate:,.2f}")