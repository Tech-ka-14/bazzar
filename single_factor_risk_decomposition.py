import numpy as np

def calculate_risk_components(beta, market_volatility, specific_volatility):
    """
    Decomposes total risk into systematic and specific risk components
    based on a single factor model.

    Parameters:
    beta (float): Sensitivity to the market factor.
    market_volatility (float): Standard deviation of the market factor (sqrt(V(X))).
    specific_volatility (float): Standard deviation of the specific risk (sqrt(V(epsilon))).

    Returns:
    dict: A dictionary containing the decomposed variances and risks.
    """
    # Systematic Risk = beta * sqrt(V(X))
    systematic_risk = beta * market_volatility
    
    # Specific Risk = sqrt(V(epsilon))
    specific_risk = specific_volatility
    
    # Calculate Variances (which are additive)
    systematic_variance = systematic_risk ** 2
    specific_variance = specific_risk ** 2
    
    # Total Variance = Systematic Variance + Specific Variance (Eq II.1.15)
    total_variance = systematic_variance + specific_variance
    
    # Total Risk = sqrt(Systematic Risk^2 + Specific Risk^2) (Eq II.1.16)
    total_risk = np.sqrt(total_variance)
    
    return {
        "systematic_risk": systematic_risk,
        "specific_risk": specific_risk,
        "systematic_variance": systematic_variance,
        "specific_variance": specific_variance,
        "total_variance": total_variance,
        "total_risk": total_risk
    }

if __name__ == "__main__":
    # --- Example Application ---
    # Suppose an asset has a beta of 1.2 to the market.
    # The market volatility is 15% and the asset's specific volatility is 10%.
    beta_asset = 1.2
    vol_market = 0.15      
    vol_specific = 0.10    
    
    risk_profile = calculate_risk_components(beta_asset, vol_market, vol_specific)
    
    print("--- Single Factor Risk Decomposition ---")
    print(f"Systematic Risk: {risk_profile['systematic_risk'] * 100:.2f}%")
    print(f"Specific Risk:   {risk_profile['specific_risk'] * 100:.2f}%")
    print("-" * 38)
    print(f"Total Variance:  {risk_profile['total_variance']:.4f}")
    print(f"Total Risk:      {risk_profile['total_risk'] * 100:.2f}%")