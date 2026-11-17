"""Correlated Monte Carlo simulation of joint asset returns.

Draws correlated Normal or Student-t vectors via the Cholesky decomposition
of a covariance matrix (Example I.5.10, Alexander 2008). Uses the legacy
global ``numpy.random`` RNG; callers seed it explicitly for reproducibility.
"""

import numpy as np


def simulate_correlated_normals(means, cov_matrix, num_simulations):
    """
    Simulates correlated normal variables using the Cholesky decomposition.

    Parameters:
    means (numpy.ndarray): 1D array of expected returns for each asset.
    cov_matrix (numpy.ndarray): 2D positive-definite covariance matrix.
    num_simulations (int): Number of joint simulations to generate.

    Returns:
    numpy.ndarray: An array of shape (num_simulations, num_assets) with correlated returns.
    """
    num_assets = len(means)

    # 1. Find the Cholesky decomposition (Lower triangular matrix C)
    C = np.linalg.cholesky(cov_matrix)

    # 2. Generate independent standard normal variables (Z)
    Z = np.random.standard_normal((num_assets, num_simulations))

    # 3. Apply the Cholesky matrix to introduce correlation and add the means
    # Formula: X = C * Z + means
    correlated_simulations = (C @ Z).T + means

    return correlated_simulations


def simulate_correlated_student_t(means, cov_matrix, degrees_of_freedom, num_simulations):
    """
    Simulates correlated Student t variables.

    Parameters:
    means (numpy.ndarray): 1D array of expected returns for each asset.
    cov_matrix (numpy.ndarray): 2D positive-definite covariance/scale matrix.
    degrees_of_freedom (list or float): Degrees of freedom for the t-distribution.
    num_simulations (int): Number of joint simulations to generate.
    """
    num_assets = len(means)
    C = np.linalg.cholesky(cov_matrix)

    # Generate independent standard Student t variables
    # Note: If df is a scalar, it applies the same df to all.
    # If it's an array, it simulates each asset with its own df.
    Z = np.random.standard_t(df=degrees_of_freedom, size=(num_assets, num_simulations))

    # Apply correlation structure
    correlated_simulations = (C @ Z).T + means

    return correlated_simulations


def compute(means, cov_matrix, num_simulations: int = 1000, seed: int = None) -> dict:
    """Standard facade: seeded correlated-normal simulation as a JSON dict.

    Parameters:
    means: 1-D array-like of expected returns per asset.
    cov_matrix: 2-D positive-definite covariance matrix (array-like).
    num_simulations (int): Number of joint scenarios to generate.
    seed (int, optional): Seed for the legacy global ``numpy.random`` RNG
    (the simulation functions use it); ``None`` leaves the RNG unseeded.

    Returns:
    dict: {"model", "num_simulations", "num_assets", "seed",
    "simulated_returns"} with the simulated matrix as nested lists.
    """
    means = np.asarray(means, dtype=float).ravel()
    cov_matrix = np.asarray(cov_matrix, dtype=float)
    if cov_matrix.shape != (means.size, means.size):
        raise ValueError("cov_matrix must be square with side len(means)")
    if int(num_simulations) < 1:
        raise ValueError("num_simulations must be a positive integer")

    if seed is not None:
        np.random.seed(int(seed))
    simulated = simulate_correlated_normals(means, cov_matrix, int(num_simulations))
    return {
        "model": "montecarlo",
        "num_simulations": int(num_simulations),
        "num_assets": int(means.size),
        "seed": None if seed is None else int(seed),
        "simulated_returns": simulated.tolist(),
    }


if __name__ == "__main__":
    # Example I.5.10 / Table I.5.4 Implementation
    np.random.seed(42)

    # Expected Returns
    means = np.array([0.07, 0.12, 0.10])

    # Volatilities
    vols = np.array([0.20, 0.30, 0.25])

    # Correlation Matrix
    corr_matrix = np.array([[1.00, 0.50, 0.75], [0.50, 1.00, 0.25], [0.75, 0.25, 1.00]])

    # Construct Covariance Matrix (V = D * C * D)
    D = np.diag(vols)
    cov_matrix = D @ corr_matrix @ D

    # Simulate 10 correlated normal returns
    simulated_returns = simulate_correlated_normals(means, cov_matrix, num_simulations=10)

    print("--- Correlated Normal Simulations ---")
    print("Asset 1 | Asset 2 | Asset 3")
    for row in simulated_returns:
        print(f"{row[0]:7.4f} | {row[1]:7.4f} | {row[2]:7.4f}")
