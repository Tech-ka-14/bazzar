"""N-asset portfolio optimization (Markowitz).

Global minimum variance weights from the inverse covariance matrix:
w = V^{-1} 1 / (1' V^{-1} 1), min variance = 1 / (1' V^{-1} 1); and the
Markowitz target-return portfolio solved via the augmented first-order
system (Equation I.6.36, Alexander 2008).
"""

import numpy as np


def global_minimum_variance_portfolio(cov_matrix):
    """
    Calculates the Global Minimum Variance portfolio weights for n assets.
    """
    # Invert the covariance matrix (V^-1)
    V_inv = np.linalg.inv(cov_matrix)

    # Sum of elements in each column (psi_i)
    psi = np.sum(V_inv, axis=0)

    # Sum of all psi elements
    sum_psi = np.sum(psi)

    # Calculate weights and resulting minimum variance
    weights = psi / sum_psi
    min_variance = 1.0 / sum_psi

    return weights, min_variance


def markowitz_target_return_portfolio(cov_matrix, expected_returns, target_return):
    """
    Solves the Markowitz problem to find weights that minimize variance
    while achieving a specific target return.
    """
    n = len(expected_returns)
    V = np.array(cov_matrix)
    E_r = np.array(expected_returns).reshape(n, 1)
    ones = np.ones((n, 1))

    # Build the augmented matrix (Eq I.6.36)
    top_left = 2 * V

    row1 = np.hstack((top_left, ones, E_r))
    row2 = np.hstack((ones.T, [[0]], [[0]]))
    row3 = np.hstack((E_r.T, [[0]], [[0]]))

    augmented_matrix = np.vstack((row1, row2, row3))

    # Build the Right-Hand Side vector
    rhs = np.zeros(n + 2)
    rhs[n] = 1.0  # Sum of weights = 1
    rhs[n + 1] = target_return  # Target return constraint

    # Solve the linear system
    solution = np.linalg.inv(augmented_matrix) @ rhs

    # Extract weights (ignoring the two Lagrange multipliers at the end)
    optimal_weights = solution[:n]
    return optimal_weights


def compute(data, target_return: float = None) -> dict:
    """Standard facade: GMV (and optionally Markowitz) weights as a JSON dict.

    Parameters:
    data: 2-D array-like (T observations x n assets) of returns used to
    estimate the covariance matrix and the expected returns.
    target_return (float, optional): When supplied, also solves the
    Markowitz minimum-variance portfolio for this target expected return
    (per-period, matching the frequency of data).

    Returns:
    dict: {"n_assets", "n_observations", "gmv_weights", "gmv_variance",
    "gmv_volatility", "target_return", "markowitz_weights"}; the last two
    are None unless target_return is supplied.
    """
    data = np.asarray(data, dtype=float)
    if data.ndim != 2 or data.shape[0] <= data.shape[1]:
        raise ValueError("data must be a 2-D array with more observations than assets")

    cov_matrix = np.cov(data, rowvar=False)
    gmv_weights, gmv_variance = global_minimum_variance_portfolio(cov_matrix)

    markowitz_weights = None
    if target_return is not None:
        expected_returns = np.mean(data, axis=0)
        markowitz_weights = [
            float(w)
            for w in markowitz_target_return_portfolio(
                cov_matrix, expected_returns, float(target_return)
            )
        ]

    return {
        "n_assets": int(data.shape[1]),
        "n_observations": int(data.shape[0]),
        "gmv_weights": [float(w) for w in gmv_weights],
        "gmv_variance": float(gmv_variance),
        "gmv_volatility": float(np.sqrt(gmv_variance)),
        "target_return": None if target_return is None else float(target_return),
        "markowitz_weights": markowitz_weights,
    }


if __name__ == "__main__":
    # --- Example I.6.8 Implementation ---
    # Assets X, Y, Z
    expected_returns = [0.05, 0.06, 0.00]
    target = 0.06

    # Reconstructing the covariance matrix from the augmented matrix in the text
    cov_matrix = np.array(
        [[0.0225, 0.0150, -0.0420], [0.0150, 0.0400, -0.0320], [-0.0420, -0.0320, 0.1600]]
    )

    opt_weights = markowitz_target_return_portfolio(cov_matrix, expected_returns, target)

    print("--- Markowitz Target Return Portfolio ---")
    print(f"Target Return: {target * 100}%")
    print(f"Weight Asset X: {opt_weights[0] * 100:.2f}%")
    print(f"Weight Asset Y: {opt_weights[1] * 100:.2f}%")
    print(f"Weight Asset Z: {opt_weights[2] * 100:.2f}%")
