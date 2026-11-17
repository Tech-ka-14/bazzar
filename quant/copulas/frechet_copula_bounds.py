"""Fréchet copula bounds.

For uniform marginals u1, u2: independence copula C = u1 u2; Fréchet upper
bound W = min(u1, u2) (perfect positive dependence); Fréchet lower bound
M = max(u1 + u2 - 1, 0) (perfect negative dependence).
"""

import numpy as np


def calculate_frechet_bounds(u1, u2):
    """
    Calculates the Independence copula, Fréchet Upper Bound, and
    Fréchet Lower Bound for a given pair of uniform marginal probabilities.
    """
    # Ensure inputs are scalar floats or numpy arrays
    u1 = np.asarray(u1)
    u2 = np.asarray(u2)

    # 1. Independence Copula
    independence = u1 * u2

    # 2. Fréchet Upper Bound (Perfect Positive Dependence)
    upper_bound = np.minimum(u1, u2)

    # 3. Fréchet Lower Bound (Perfect Negative Dependence)
    lower_bound = np.maximum(u1 + u2 - 1, 0)

    return {
        "Independence (C)": independence,
        "Fréchet Upper Bound (W)": upper_bound,
        "Fréchet Lower Bound (M)": lower_bound,
    }


def compute(u1: float, u2: float) -> dict:
    """Standard facade: Fréchet bounds at a scalar point as a JSON dict.

    Parameters:
    u1 (float): First uniform marginal probability in [0, 1].
    u2 (float): Second uniform marginal probability in [0, 1].

    Returns:
    dict: {"u1", "u2", "independence", "frechet_upper_bound",
    "frechet_lower_bound"} with plain floats.
    """
    u1 = float(u1)
    u2 = float(u2)
    if not 0.0 <= u1 <= 1.0 or not 0.0 <= u2 <= 1.0:
        raise ValueError("u1 and u2 must lie in the closed interval [0, 1]")

    bounds = calculate_frechet_bounds(u1, u2)
    return {
        "u1": u1,
        "u2": u2,
        "independence": float(bounds["Independence (C)"]),
        "frechet_upper_bound": float(bounds["Fréchet Upper Bound (W)"]),
        "frechet_lower_bound": float(bounds["Fréchet Lower Bound (M)"]),
    }


if __name__ == "__main__":
    # Example Evaluation at the median:
    # What are the bounds when both variables are exactly at their 50th percentile?
    bounds_at_median = calculate_frechet_bounds(0.50, 0.50)
    print(bounds_at_median)
    # Output: C = 0.25 (Independent), W = 0.50 (Perfect Positive), M = 0.0 (Perfect Negative)
