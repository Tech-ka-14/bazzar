"""Principal component VaR of a yield-curve portfolio.

Eigendecomposes the risk-factor covariance matrix, maps the PV01 vector
onto the p leading principal components, and computes normal linear VaR
in the reduced factor space.
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.2.5.
"""

import numpy as np
from scipy.stats import norm


def calculate_pc_var(
    theta: np.ndarray, covariance_matrix: np.ndarray, num_components: int, alpha: float = 0.01
):
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
    lambda_p = np.diag(eigenvalues[:num_components])  # p x p diagonal matrix
    w_p = eigenvectors[:, :num_components]  # n x p matrix

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


def compute(theta, covariance_matrix, num_components: int = 3, alpha: float = 0.01) -> dict:
    """Standard facade: principal component VaR as a JSON-serializable dict.

    Parameters:
    theta: 1-D array-like of PV01 sensitivities (n risk factors).
    covariance_matrix: Square covariance matrix matching len(theta).
    num_components (int): Number p of principal components to retain.
    alpha (float): Tail probability in (0, 1), e.g. 0.01.

    Returns:
    dict: {"method", "alpha", "n_factors", "num_components", "var",
    "explained_variance"}.
    """
    theta = np.asarray(theta, dtype=float).ravel()
    cov = np.asarray(covariance_matrix, dtype=float)
    if theta.size == 0:
        raise ValueError("theta must contain at least one sensitivity")
    if cov.shape != (theta.size, theta.size):
        raise ValueError("covariance_matrix must be square with size len(theta)")
    if not 1 <= num_components <= theta.size:
        raise ValueError("num_components must be between 1 and len(theta)")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    pc_var, explained = calculate_pc_var(theta, cov, int(num_components), float(alpha))
    return {
        "method": "principal_component",
        "alpha": float(alpha),
        "n_factors": int(theta.size),
        "num_components": int(num_components),
        "var": float(pc_var),
        "explained_variance": float(explained),
    }


if __name__ == "__main__":
    num_vertices = 60
    np.random.seed(42)  # Seed for reproducibility

    # 1. Recreate a slice of the PV01 vector from Figure IV.2.2 (first 10 months for brevity + zeros)
    # In reality, this would be the exact 60-item array from the table
    theta_60m = np.zeros(num_vertices)
    sample_pv01s = [0.6, 0.3, 0.2, -1.6, -0.7, -1.8, 0.7, -3.0, -0.1, 0.3]
    theta_60m[: len(sample_pv01s)] = sample_pv01s
    # Converting £000s to raw pounds
    theta_60m = theta_60m * 1000

    # 2. Create a mock highly-collinear 60x60 covariance matrix (typical of yield curves)
    # Generating a correlation matrix where close maturities are highly correlated
    base_vol = 50  # basis points
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
    confidence = 0.01  # 1% VaR

    pc_var_estimate, var_explained = calculate_pc_var(
        theta=theta_60m, covariance_matrix=cov_matrix_60m, num_components=n_pcs, alpha=confidence
    )

    print("--- Principal Component VaR Analysis ---")
    print(f"Original Dimensions: {num_vertices} Risk Factors")
    print(f"Reduced Dimensions: {n_pcs} Principal Components")
    print(f"Total System Variance Captured: {var_explained:.2%}")
    print(f"1% PC VaR Estimate: £{pc_var_estimate:,.2f}")
