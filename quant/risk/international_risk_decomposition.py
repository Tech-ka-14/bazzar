"""International portfolio risk decomposition.

Decomposes the systematic variance of an international portfolio into
equity, FX and quanto (equity-FX covariance) components via the
partitioned covariance matrix of equity and FX risk factors.
Reference: Alexander (2008), Market Risk Analysis II, Example II.1.6.
"""

import numpy as np


def international_portfolio_risk(weights, asset_betas, omega_matrix, num_equity_factors):
    """
    Decomposes international portfolio variance into Equity, FX, and Quanto components.

    Parameters:
    weights (numpy.ndarray): Portfolio weights for each country index.
    asset_betas (numpy.ndarray): Beta of each country's investment to its local market index.
    omega_matrix (numpy.ndarray): Full covariance matrix of all risk factors (Equity then FX).
    num_equity_factors (int): The number of equity market factors (k).

    Returns:
    dict: Decomposition of systematic variance.
    """
    # 1. Prepare the effective beta vector (tilde_beta) and foreign weight vector (tilde_w)
    # tilde_beta = w_i * beta_i for all equity factors
    tilde_beta = weights * asset_betas

    # tilde_w = weights of the foreign assets only (assumes first asset is domestic)
    tilde_w = weights[1:]

    # 2. Partition the Covariance Matrix
    # Omega_E: Equity covariance matrix (top left block)
    Omega_E = omega_matrix[:num_equity_factors, :num_equity_factors]

    # Omega_X: Forex covariance matrix (bottom right block)
    Omega_X = omega_matrix[num_equity_factors:, num_equity_factors:]

    # Omega_EX: Quanto (Equity-Forex) covariance matrix (top right block)
    Omega_EX = omega_matrix[:num_equity_factors, num_equity_factors:]

    # 3. Calculate Variance Components
    equity_variance = tilde_beta.T @ Omega_E @ tilde_beta
    fx_variance = tilde_w.T @ Omega_X @ tilde_w

    # Note: the 2 multiplier accounts for both Omega_EX and Omega_XE
    quanto_covariance = 2 * (tilde_beta.T @ Omega_EX @ tilde_w)

    total_systematic_variance = equity_variance + fx_variance + quanto_covariance

    return {
        "equity_variance": float(equity_variance),
        "fx_variance": float(fx_variance),
        "quanto_covariance": float(quanto_covariance),
        "total_systematic_variance": float(total_systematic_variance),
        "total_systematic_risk": float(np.sqrt(total_systematic_variance)),
    }


def compute(weights, asset_betas, omega_matrix, num_equity_factors: int) -> dict:
    """Standard facade: international risk decomposition as a JSON dict.

    Parameters:
    weights: 1-D array-like of country weights (first entry domestic).
    asset_betas: 1-D array-like of betas to local market indices.
    omega_matrix: Full covariance matrix of equity then FX factors.
    num_equity_factors (int): Number k of equity market factors; the
    remaining rows/columns are the FX factors.

    Returns:
    dict: {"method", "equity_variance", "fx_variance",
    "quanto_covariance", "total_systematic_variance",
    "total_systematic_risk"}.
    """
    weights = np.asarray(weights, dtype=float).ravel()
    betas = np.asarray(asset_betas, dtype=float).ravel()
    omega = np.asarray(omega_matrix, dtype=float)
    k = int(num_equity_factors)
    if weights.size != betas.size:
        raise ValueError("weights and asset_betas must have equal length")
    if not 1 <= k <= weights.size:
        raise ValueError("num_equity_factors must be in [1, len(weights)]")
    n_total = k + (weights.size - 1)  # k equity factors + one FX factor per foreign asset
    if omega.shape != (n_total, n_total):
        raise ValueError("omega_matrix has inconsistent dimensions")

    results = international_portfolio_risk(weights, betas, omega, k)
    results["method"] = "international_decomposition"
    return results


if __name__ == "__main__":
    # --- Example II.1.6 Implementation ---
    # Weights: UK (Domestic), US (Foreign), Germany (Foreign)
    w = np.array([0.5, 0.2, 0.3])
    betas = np.array([1.5, 1.2, 0.8])

    # Full 5x5 Covariance Matrix (FTSE, S&P, DAX, USD/GBP, EUR/GBP)
    omega = np.array(
        [
            [0.0400, 0.0352, 0.0350, 0.0040, 0.0072],
            [0.0352, 0.0484, 0.0330, -0.0055, 0.00132],
            [0.0350, 0.0330, 0.0625, 0.00125, -0.0045],
            [0.0040, -0.0055, 0.00125, 0.0100, 0.0072],
            [0.0072, 0.00132, -0.0045, 0.0072, 0.0144],
        ]
    )

    results = international_portfolio_risk(w, betas, omega, num_equity_factors=3)

    print("--- International Risk Decomposition ---")
    print(f"Equity Variance: {results['equity_variance']:.6f}")
    print(f"FX Variance:     {results['fx_variance']:.6f}")
    print(f"Quanto Covar:    {results['quanto_covariance']:.6f}")
    print("-" * 35)
    print(f"Total Sys Var:   {results['total_systematic_variance']:.6f}")
    print(f"Total Sys Risk:  {results['total_systematic_risk'] * 100:.2f}%")
