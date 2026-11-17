"""Fundamental factor sensitivity estimation.

OLS regression of an asset's returns on k fundamental factor returns
(e.g. Market, Industry, Growth, Cap): R_i = alpha + beta' F + epsilon,
yielding the factor betas, R-squared and the idiosyncratic specific risk.
"""

import numpy as np
import statsmodels.api as sm


def estimate_fundamental_factors(asset_returns, fundamental_factors):
    """
    Estimates the sensitivities (betas) of an asset to various fundamental risk factors.

    Parameters:
    asset_returns (numpy.ndarray): 1D array of the asset's log returns.
    fundamental_factors (numpy.ndarray): 2D array (T x k) of the fundamental factor returns
                                         (e.g., Market, Industry, Growth, Cap).

    Returns:
    dict: A dictionary containing the estimated Alpha, Betas, and R-squared.
    """
    # Add a constant term to estimate the Alpha
    X = sm.add_constant(fundamental_factors)

    # Fit the OLS model
    model = sm.OLS(asset_returns, X).fit()

    # Extract Alpha and Betas
    alpha = model.params[0]
    betas = model.params[1:]

    return {
        "alpha": float(alpha),
        "betas": betas.flatten(),
        "r_squared": float(model.rsquared),
        "specific_risk": float(np.std(model.resid, ddof=1)),  # Idiosyncratic volatility
    }


def compute(asset_returns, fundamental_factors) -> dict:
    """Standard facade: fundamental factor sensitivities as a JSON dict.

    Parameters:
    asset_returns: 1-D array-like of the asset's returns (T).
    fundamental_factors: 2-D array-like (T x k) of fundamental factor
    returns.

    Returns:
    dict: {"n_observations", "n_factors", "alpha", "betas", "r_squared",
    "specific_risk"} with plain floats/lists.
    """
    asset_returns = np.asarray(asset_returns, dtype=float).ravel()
    fundamental_factors = np.asarray(fundamental_factors, dtype=float)
    if fundamental_factors.ndim == 1:
        fundamental_factors = fundamental_factors.reshape(-1, 1)
    if asset_returns.size != fundamental_factors.shape[0] or asset_returns.size < 3:
        raise ValueError("asset_returns must match the factor row count and have length >= 3")

    results = estimate_fundamental_factors(asset_returns, fundamental_factors)
    return {
        "n_observations": int(asset_returns.size),
        "n_factors": int(fundamental_factors.shape[1]),
        "alpha": float(results["alpha"]),
        "betas": [float(b) for b in np.asarray(results["betas"], dtype=float).ravel()],
        "r_squared": float(results["r_squared"]),
        "specific_risk": float(results["specific_risk"]),
    }


if __name__ == "__main__":
    # --- Example Implementation ---
    # Simulating the Case Study setup: 100 periods of returns
    np.random.seed(42)
    T = 100

    # 4 Fundamental Factors: Market, Communications (Industry), Growth, Large Cap
    market = np.random.normal(0.005, 0.04, T)
    industry = np.random.normal(0.002, 0.03, T)
    growth = np.random.normal(0.001, 0.02, T)
    large_cap = np.random.normal(0.0015, 0.015, T)

    factors = np.column_stack((market, industry, growth, large_cap))

    # Simulate an asset (e.g., Vodafone) with specific sensitivities to these factors
    # True betas: Market=1.1, Industry=0.8, Growth=0.2, Cap=0.5
    asset = (
        0.001
        + 1.1 * market
        + 0.8 * industry
        + 0.2 * growth
        + 0.5 * large_cap
        + np.random.normal(0, 0.01, T)
    )

    results = estimate_fundamental_factors(asset, factors)

    print("--- Fundamental Factor Sensitivities ---")
    print(f"Alpha:         {results['alpha']:.6f}")
    print(f"Market Beta:   {results['betas'][0]:.4f}")
    print(f"Industry Beta: {results['betas'][1]:.4f}")
    print(f"Growth Beta:   {results['betas'][2]:.4f}")
    print(f"Cap Beta:      {results['betas'][3]:.4f}")
    print(f"Model R^2:     {results['r_squared']:.4f}")
