"""Spearman's rank correlation.

rho = 1 - 6 D / (n (n^2 - 1)) where D is the sum of squared rank
differences; ties receive the average of their ranks. Reference: Alexander
(2008), Vol. II, Example II.6.1.
"""

import numpy as np
from scipy.stats import rankdata


def calculate_spearman_rho(x, y):
    """
    Calculates Spearman's rank correlation coefficient.
    Handles tied values by assigning them the average of their ranks.
    """
    n = len(x)

    # 1. Rank the data (rankdata automatically uses the 'average' method for ties)
    rank_x = rankdata(x)
    rank_y = rankdata(y)

    # 2. Calculate the squared differences between the ranks (d_i^2)
    squared_diffs = (rank_x - rank_y) ** 2

    # 3. Sum the squared differences (D)
    D = np.sum(squared_diffs)

    # 4. Apply Spearman's formula
    rho = 1 - (6 * D) / (n * (n**2 - 1))

    return {"D (Sum of Squared Diffs)": D, "Spearman Rho": round(rho, 4)}


def compute(data, y=None) -> dict:
    """Standard facade: Spearman's rank correlation as a JSON dict.

    Parameters:
    data: 1-D array-like of x observations.
    y: 1-D array-like of y observations (same length, >= 2).

    Returns:
    dict: {"n", "d_squared_sum", "spearman_rho"}.
    """
    if y is None:
        raise ValueError("y is required")
    x = np.asarray(data, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    if x.shape != y.shape or x.size < 2:
        raise ValueError("x and y must be equal-length arrays of size >= 2")

    result = calculate_spearman_rho(x, y)
    return {
        "n": int(x.size),
        "d_squared_sum": float(result["D (Sum of Squared Diffs)"]),
        "spearman_rho": float(result["Spearman Rho"]),
    }


if __name__ == "__main__":
    # Example II.6.1 Data from Table II.6.1
    X = np.array([50, 10, 50, -20, 20, 60, 10, 0, 90, 50])
    Y = np.array([40, -10, 20, -80, 50, 10, 10, 30, 60, 40])

    results = calculate_spearman_rho(X, Y)
    # Output matches the text exactly: D = 69.0, Rho = 0.5818
    print(results)
