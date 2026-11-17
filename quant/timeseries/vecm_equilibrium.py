"""Vector Error Correction Model (VECM) equilibrium estimation.

Determines the cointegration rank via the Johansen trace test and fits a
VECM to extract the cointegrating vectors (Beta, the long-run equilibrium
weights) and the adjustment speeds (Alpha).
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.vector_ar.vecm import VECM, select_coint_rank


def estimate_vecm(price_matrix, k_ar_diff=1):
    """
    Estimates the Vector Error Correction Model (VECM) to extract
    the cointegrating vectors (Beta) and the speed of adjustment (Alpha).
    """
    # Step 1: Automatically determine the cointegration rank
    rank_test = select_coint_rank(
        price_matrix, det_order=0, k_ar_diff=k_ar_diff, method="trace", signif=0.05
    )
    optimal_rank = rank_test.rank

    if optimal_rank == 0:
        return {"Error": "No cointegration found in the portfolio. Cannot estimate VECM."}

    # Step 2: Fit the VECM using the determined rank
    vecm_model = VECM(
        price_matrix, k_ar_diff=k_ar_diff, coint_rank=optimal_rank, deterministic="ci"
    )
    vecm_fit = vecm_model.fit()

    # Step 3: Extract Alpha and Beta matrices
    # Beta (Cointegrating Vectors): The weights establishing the long-term equilibrium
    beta_matrix = vecm_fit.beta

    # Alpha (Speed of Adjustment): How fast each asset pulls back to the equilibrium
    alpha_matrix = vecm_fit.alpha

    # Step 4: Return formatted results
    asset_names = price_matrix.columns

    return {
        "Cointegration Rank (r)": optimal_rank,
        "Beta (Equilibrium Weights)": pd.DataFrame(
            beta_matrix,
            index=asset_names,
            columns=[f"Equation {i + 1}" for i in range(optimal_rank)],
        ),
        "Alpha (Adjustment Speeds)": pd.DataFrame(
            alpha_matrix,
            index=asset_names,
            columns=[f"Equation {i + 1}" for i in range(optimal_rank)],
        ),
        "Model Summary": vecm_fit.summary(),
    }


def compute(price_matrix, k_ar_diff: int = 1) -> dict:
    """Standard facade: VECM cointegration results as a JSON dict.

    Parameters:
    price_matrix: pandas DataFrame (or dict of equal-length column lists) of
    asset prices; each column is one asset.
    k_ar_diff (int): Number of lagged differences in the VECM (>= 1).

    Returns:
    dict: {"cointegration_rank", "assets", "beta", "alpha"} with beta and
    alpha as nested lists (rows = assets, columns = cointegration equations).
    When no cointegration is found the rank is 0 and beta/alpha are empty.
    """
    if not isinstance(price_matrix, pd.DataFrame):
        price_matrix = pd.DataFrame(price_matrix)
    k_ar_diff = int(k_ar_diff)
    if k_ar_diff < 1:
        raise ValueError("k_ar_diff must be at least 1")
    if price_matrix.shape[1] < 2:
        raise ValueError("price_matrix must contain at least two asset columns")

    results = estimate_vecm(price_matrix, k_ar_diff=k_ar_diff)
    if "Error" in results:
        return {
            "cointegration_rank": 0,
            "assets": [str(c) for c in price_matrix.columns],
            "beta": [],
            "alpha": [],
            "status": "no_cointegration",
        }

    beta = np.asarray(results["Beta (Equilibrium Weights)"].to_numpy(), dtype=float)
    alpha = np.asarray(results["Alpha (Adjustment Speeds)"].to_numpy(), dtype=float)
    return {
        "cointegration_rank": int(results["Cointegration Rank (r)"]),
        "assets": [str(c) for c in price_matrix.columns],
        "beta": beta.tolist(),
        "alpha": alpha.tolist(),
        "status": "ok",
    }


# Example Usage:
# vecm_results = estimate_vecm(portfolio_prices)
