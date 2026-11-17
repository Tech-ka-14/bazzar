"""Monte Carlo Value at Risk from a simulated return matrix.

Aggregates simulated asset returns into portfolio scenarios with fixed
weights and reads the empirical alpha-percentile of the simulated portfolio
return distribution; VaR is the negative of that percentile (Example II.6.5,
Alexander 2008).
"""

import numpy as np


def calculate_copula_var(simulated_returns_matrix, portfolio_weights, confidence_level=0.01):
    """
    Calculates the Monte Carlo Value-at-Risk (VaR) for a portfolio
    whose asset returns were generated via a copula simulation.

    simulated_returns_matrix: 2D array of returns (n_simulations x n_assets).
    portfolio_weights: 1D array of portfolio weights (must sum to 1).
    confidence_level: The risk tail probability (e.g., 0.01 for 1% VaR).
    """
    # 1. Calculate the simulated portfolio returns for each scenario
    # R_p = w_1*R_1 + w_2*R_2 + ... + w_n*R_n
    portfolio_returns = np.dot(simulated_returns_matrix, portfolio_weights)

    # 2. Extract the empirical percentile representing the VaR
    # (Multiply by 100 to get the exact percentile index, e.g., 0.01 -> 1st percentile)
    var_percentile = np.percentile(portfolio_returns, confidence_level * 100)

    # 3. VaR is typically expressed as a positive number representing the loss
    portfolio_var = -var_percentile

    return {
        "Confidence Level": f"{(1 - confidence_level) * 100}%",
        "Estimated VaR (Decimal)": portfolio_var,
        "Estimated VaR (%)": round(portfolio_var * 100, 2),
    }


def compute(simulated_returns, weights=None, confidence: float = 0.99) -> dict:
    """Standard facade: Monte Carlo VaR from simulated returns as a JSON dict.

    Parameters:
    simulated_returns: 2-D array-like (n_simulations x n_assets) of
    simulated returns, or 1-D for a single asset.
    weights: optional 1-D array-like of portfolio weights; defaults to
    equal weights across assets.
    confidence (float): Confidence level in (0, 1), e.g. 0.99.

    Returns:
    dict: {"method", "confidence", "n_simulations", "n_assets", "var"}
    with "var" the positive loss fraction.
    """
    simulated_returns = np.asarray(simulated_returns, dtype=float)
    if simulated_returns.ndim == 1:
        simulated_returns = simulated_returns.reshape(-1, 1)
    if simulated_returns.ndim != 2 or min(simulated_returns.shape) < 1:
        raise ValueError("simulated_returns must be a non-empty 1-D or 2-D array")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in the open interval (0, 1)")

    n_simulations, n_assets = simulated_returns.shape
    if weights is None:
        weights = np.full(n_assets, 1.0 / n_assets)
    weights = np.asarray(weights, dtype=float).ravel()
    if weights.size != n_assets:
        raise ValueError("weights must have one entry per asset (column)")

    alpha = 1.0 - float(confidence)
    raw = calculate_copula_var(simulated_returns, weights, confidence_level=alpha)
    return {
        "method": "montecarlo",
        "confidence": float(confidence),
        "n_simulations": int(n_simulations),
        "n_assets": int(n_assets),
        "var": float(raw["Estimated VaR (Decimal)"]),
    }


# Example Usage mapping to Example II.6.5:
# weights = np.array([0.75, 0.25])
# var_metrics = calculate_copula_var(simulated_returns, weights, confidence_level=0.01)
# print(var_metrics)
