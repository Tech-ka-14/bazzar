import numpy as np
import pandas as pd
from statsmodels.tsa.vector_ar.vecm import VECM, select_coint_rank

def estimate_vecm(price_matrix, k_ar_diff=1):
    """
    Estimates the Vector Error Correction Model (VECM) to extract 
    the cointegrating vectors (Beta) and the speed of adjustment (Alpha).
    """
    # Step 1: Automatically determine the cointegration rank
    rank_test = select_coint_rank(price_matrix, det_order=0, k_ar_diff=k_ar_diff, method='trace', signif=0.05)
    optimal_rank = rank_test.rank
    
    if optimal_rank == 0:
        return {"Error": "No cointegration found in the portfolio. Cannot estimate VECM."}
    
    # Step 2: Fit the VECM using the determined rank
    vecm_model = VECM(price_matrix, k_ar_diff=k_ar_diff, coint_rank=optimal_rank, deterministic='ci')
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
        "Beta (Equilibrium Weights)": pd.DataFrame(beta_matrix, index=asset_names, columns=[f"Equation {i+1}" for i in range(optimal_rank)]),
        "Alpha (Adjustment Speeds)": pd.DataFrame(alpha_matrix, index=asset_names, columns=[f"Equation {i+1}" for i in range(optimal_rank)]),
        "Model Summary": vecm_fit.summary()
    }

# Example Usage:
# vecm_results = estimate_vecm(portfolio_prices)