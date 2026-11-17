"""Style attribution via constrained least squares.

Sharpe's returns-based style analysis: minimizes the sum of squared
residuals of fund returns regressed on style index returns, subject to the
style weights summing to 1 and lying in [0, 1] (no shorting).
"""

import numpy as np
from scipy.optimize import minimize


def style_attribution_analysis(fund_returns, style_factors):
    """
    Performs style attribution using constrained least squares optimization.

    Parameters:
    fund_returns (numpy.ndarray): 1D array of the fund's historical returns (T x 1).
    style_factors (numpy.ndarray): 2D array of returns for the style indices (T x k).

    Returns:
    numpy.ndarray: The estimated style weights summing to 1.
    """
    k = style_factors.shape[1]

    # Objective Function: Sum of Squared Residuals
    def objective(beta):
        residuals = fund_returns - (style_factors @ beta)
        return np.sum(residuals**2)

    # Constraint: Weights must sum to 1
    constraints = {"type": "eq", "fun": lambda beta: np.sum(beta) - 1.0}

    # Bounds: Weights must be >= 0 (no shorting of styles)
    bounds = [(0.0, 1.0) for _ in range(k)]

    # Initial Guess: Equal weighting
    initial_guess = np.ones(k) / k

    # Run the SLSQP optimizer
    result = minimize(
        objective, initial_guess, method="SLSQP", bounds=bounds, constraints=constraints
    )

    if not result.success:
        raise ValueError("Optimization failed to converge.")

    return result.x


def compute(fund_returns, style_factors) -> dict:
    """Standard facade: style attribution weights as a JSON dict.

    Parameters:
    fund_returns: 1-D array-like of the fund's historical returns (T).
    style_factors: 2-D array-like (T x k) of style index returns.

    Returns:
    dict: {"n_observations", "n_styles", "style_weights"} with the
    constrained weights (summing to 1, each in [0, 1]) as plain floats.
    """
    fund_returns = np.asarray(fund_returns, dtype=float).ravel()
    style_factors = np.asarray(style_factors, dtype=float)
    if style_factors.ndim != 2:
        raise ValueError("style_factors must be a 2-D array (T x k)")
    if fund_returns.size != style_factors.shape[0] or fund_returns.size < 3:
        raise ValueError("fund_returns must match the style row count and have length >= 3")

    weights = style_attribution_analysis(fund_returns, style_factors)
    return {
        "n_observations": int(fund_returns.size),
        "n_styles": int(style_factors.shape[1]),
        "style_weights": [float(w) for w in weights],
    }


if __name__ == "__main__":
    # Synthetic data for T=100 days, k=4 style factors
    np.random.seed(42)
    T = 100

    # Simulate 4 style factors
    R1000V = np.random.normal(0.0005, 0.01, T)
    R1000G = np.random.normal(0.0006, 0.012, T)
    R2000V = np.random.normal(0.0007, 0.015, T)
    R2000G = np.random.normal(0.0008, 0.018, T)

    styles = np.column_stack((R1000V, R1000G, R2000V, R2000G))

    # Simulate a fund that is effectively 60% R1000V and 40% R2000G with some noise
    fund = 0.60 * R1000V + 0.40 * R2000G + np.random.normal(0, 0.002, T)

    estimated_weights = style_attribution_analysis(fund, styles)

    print("--- Style Attribution Weights ---")
    print(f"Russell 1000 Value:  {estimated_weights[0] * 100:.1f}%")
    print(f"Russell 1000 Growth: {estimated_weights[1] * 100:.1f}%")
    print(f"Russell 2000 Value:  {estimated_weights[2] * 100:.1f}%")
    print(f"Russell 2000 Growth: {estimated_weights[3] * 100:.1f}%")
