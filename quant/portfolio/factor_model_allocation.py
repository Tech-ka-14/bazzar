"""Linear factor model estimation for allocation.

OLS regression of asset returns on k factor returns:
R_i = alpha + beta' F + epsilon. The residual standard deviation is the
specific risk (tracking error proxy) used in factor-based allocation.
"""

import numpy as np
import statsmodels.api as sm


def estimate_factor_model(asset_returns, factor_returns):
    """
    Estimates the Alpha, Betas, and Tracking Error of an asset using a linear factor model.

    Parameters:
    asset_returns (numpy.ndarray): 1D array of the asset's historical returns (T x 1).
    factor_returns (numpy.ndarray): 2D array of the fundamental factors' returns (T x k).

    Returns:
    dict: A dictionary containing the estimated Alpha, Betas, and Tracking Error.
    """
    # Add a column of 1s to the factor returns to estimate the constant term (Alpha)
    X = sm.add_constant(factor_returns)

    # Fit the Ordinary Least Squares (OLS) model
    model = sm.OLS(asset_returns, X).fit()

    # Extract the parameters
    alpha = model.params[0]
    betas = model.params[1:]

    # The standard deviation of the residuals represents the specific risk (tracking error proxy)
    tracking_error = np.std(model.resid, ddof=1)

    return {
        "alpha": alpha,
        "betas": betas,
        "tracking_error": tracking_error,
        "r_squared": model.rsquared,
    }


def compute(asset_returns, factor_returns) -> dict:
    """Standard facade: factor model estimates as a JSON-serializable dict.

    Parameters:
    asset_returns: 1-D array-like of the asset's historical returns (T).
    factor_returns: 2-D array-like (T x k) of factor returns.

    Returns:
    dict: {"n_observations", "n_factors", "alpha", "betas",
    "tracking_error", "r_squared"} with plain floats/lists.
    """
    asset_returns = np.asarray(asset_returns, dtype=float).ravel()
    factor_returns = np.asarray(factor_returns, dtype=float)
    if factor_returns.ndim == 1:
        factor_returns = factor_returns.reshape(-1, 1)
    if asset_returns.size != factor_returns.shape[0] or asset_returns.size < 3:
        raise ValueError("asset_returns must match the factor row count and have length >= 3")

    results = estimate_factor_model(asset_returns, factor_returns)
    return {
        "n_observations": int(asset_returns.size),
        "n_factors": int(factor_returns.shape[1]),
        "alpha": float(results["alpha"]),
        "betas": [float(b) for b in np.asarray(results["betas"], dtype=float).ravel()],
        "tracking_error": float(results["tracking_error"]),
        "r_squared": float(results["r_squared"]),
    }


if __name__ == "__main__":
    # Synthetic Data Setup (e.g., 100 weeks of data)
    np.random.seed(42)
    T = 100

    # Two factors (e.g., S&P 500 return and Value Index return)
    market_factor = np.random.normal(0.001, 0.02, T)
    value_factor = np.random.normal(0.0005, 0.015, T)
    factors = np.column_stack((market_factor, value_factor))

    # Simulate an asset with an alpha of 0.002 (20 bps), market beta of 1.2, value beta of -0.5
    noise = np.random.normal(0, 0.01, T)
    asset_ret = 0.002 + 1.2 * market_factor - 0.5 * value_factor + noise

    results = estimate_factor_model(asset_ret, factors)

    print("--- Factor Model Results ---")
    print(f"Estimated Alpha: {results['alpha']:.4f}")
    print(f"Estimated Market Beta: {results['betas'][0]:.4f}")
    print(f"Estimated Value Beta: {results['betas'][1]:.4f}")
    print(f"Specific Risk (Tracking Error): {results['tracking_error']:.4f}")
