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
        "Estimated VaR (%)": round(portfolio_var * 100, 2)
    }

# Example Usage mapping to Example II.6.5:
# weights = np.array([0.75, 0.25])
# var_metrics = calculate_copula_var(simulated_returns, weights, confidence_level=0.01)
# print(var_metrics)