"""Monte Carlo simulation of orthogonal principal-component factors.

Draws independent normal or standardized Student-t innovations and
scales them by the square roots of the covariance eigenvalues (PCA
volatilities).
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.2.5.
"""

import numpy as np
from scipy import stats


def simulate_pca_factors(
    eigenvalues: np.ndarray, n_simulations: int, distribution: str = "normal", df: int = None
) -> np.ndarray:
    """
    Simulates orthogonal Principal Component risk factors directly from eigenvalues.
    """
    k = len(eigenvalues)

    # The Cholesky matrix of orthogonal components is just the square root of the eigenvalues
    pca_vols = np.sqrt(eigenvalues)

    if distribution == "normal":
        z = np.random.standard_normal((n_simulations, k))
    elif distribution == "student_t" and df is not None:
        u = np.random.uniform(0, 1, (n_simulations, k))
        standard_t = stats.t.ppf(u, df=df)
        z = standard_t * np.sqrt((df - 2) / df)
    else:
        raise ValueError("Invalid distribution type")

    # Scale the independent draws by the PCA volatilities
    pca_simulations = z * pca_vols
    return pca_simulations


def compute(
    eigenvalues,
    n_simulations: int = 10000,
    distribution: str = "normal",
    df: int = None,
    seed: int = None,
) -> dict:
    """Standard facade: PCA factor Monte Carlo summary as a JSON dict.

    Parameters:
    eigenvalues: 1-D array-like of positive covariance eigenvalues.
    n_simulations (int): Number of Monte Carlo draws.
    distribution (str): "normal" or "student_t".
    df (int, optional): Degrees of freedom for Student-t (> 2).
    seed (int, optional): RNG seed for reproducibility.

    Returns:
    dict: {"method", "distribution", "n_simulations", "n_factors",
    "simulated_variance_share"} — the empirical variance share of each
    simulated factor relative to the total.
    """
    eigenvalues = np.asarray(eigenvalues, dtype=float).ravel()
    if eigenvalues.size == 0 or np.any(eigenvalues <= 0):
        raise ValueError("eigenvalues must be positive and non-empty")
    if distribution == "student_t" and (df is None or df <= 2):
        raise ValueError("student_t simulation requires df > 2")
    if seed is not None:
        np.random.seed(seed)

    sims = simulate_pca_factors(eigenvalues, int(n_simulations), distribution, df)
    emp_vars = np.var(sims, axis=0)
    total = float(np.sum(emp_vars))
    return {
        "method": "pca_monte_carlo",
        "distribution": str(distribution),
        "n_simulations": int(n_simulations),
        "n_factors": int(eigenvalues.size),
        "simulated_variance_share": [float(v / total) for v in emp_vars],
    }
