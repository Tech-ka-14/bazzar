"""Covariance matrix scaling over time.

Under i.i.d. returns the h-period covariance matrix is V_h = h * V_1.
Reference: Alexander (2008), Vol. II, Example II.3.14.
"""

import numpy as np


def scale_covariance_matrix(V_1, h):
    """
    Scales a 1-period covariance matrix to an h-period forecast.

    Parameters:
    V_1 (numpy.ndarray): The 1-period covariance matrix (n x n).
    h (int): The number of periods.

    Returns:
    numpy.ndarray: The h-period covariance matrix.
    """
    return V_1 * h


def compute(data, h=1) -> dict:
    """Standard facade: scale a 1-period covariance matrix to h periods.

    Parameters:
    data: square 1-period covariance matrix (list of lists).
    h (int): number of periods (>= 1).

    Returns:
    dict: {"horizon", "scaled_covariance"}.
    """
    V = np.asarray(data, dtype=float)
    if V.ndim != 2 or V.shape[0] != V.shape[1]:
        raise ValueError("data must be a square covariance matrix")
    if int(h) < 1:
        raise ValueError("h must be a positive integer")

    scaled = scale_covariance_matrix(V, int(h))
    return {"horizon": int(h), "scaled_covariance": np.asarray(scaled).tolist()}


if __name__ == "__main__":
    # --- Example II.3.14 Implementation ---
    # Daily covariance matrix V_1
    V_1 = np.array([[21.644, 6.196], [6.196, 7.006]]) * 1e-4

    # 5-day forecast
    h = 5
    V_h = scale_covariance_matrix(V_1, h)

    print("--- Covariance Matrix Scaling ---")
    print("1-Day Covariance Matrix:")
    print(V_1)
    print("\n5-Day Covariance Matrix Forecast:")
    print(V_h)
