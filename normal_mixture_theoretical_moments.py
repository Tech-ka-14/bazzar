import numpy as np

def calculate_mixture_moments(weights: np.ndarray, means: np.ndarray, vols: np.ndarray):
    """
    Calculates the theoretical moments (Mean, Variance, Skewness, Kurtosis) 
    of a Normal Mixture Distribution (Equations IV.2.73 and IV.2.74).
    """
    # Equation IV.2.73: Non-Central Moments
    m1 = np.sum(weights * means)
    m2 = np.sum(weights * (vols**2 + means**2))
    m3 = np.sum(weights * (3 * means * vols**2 + means**3))
    m4 = np.sum(weights * (3 * vols**4 + 6 * means**2 * vols**2 + means**4))
    
    # Equation IV.2.74: Central Moments (Mean, Variance, Skewness, Kurtosis)
    mu = m1
    variance = m2 - m1**2
    sigma = np.sqrt(variance)
    
    skewness = (m3 - 3*m1*m2 + 2*m1**3) / (sigma**3)
    kurtosis = (m4 - 4*m1*m3 + 6*(m1**2)*m2 - 3*m1**4) / (sigma**4)
    
    # Note: The result is raw kurtosis. Excess kurtosis is kurtosis - 3.
    return mu, sigma, skewness, kurtosis

# Example IV.2.21: Parameters from Table IV.2.26 (Annualized)
weights_annual = np.array([0.34003, 1 - 0.34003])
means_annual = np.array([-0.3107, 0.2052])
vols_annual = np.array([0.2649, 0.0952])

mu, vol, skew, kurt = calculate_mixture_moments(weights_annual, means_annual, vols_annual)

print("--- Theoretical Moments of the Normal Mixture ---")
print(f"Mean: {mu:.4%}")
print(f"Volatility: {vol:.4%}")
print(f"Skewness: {skew:.4f}")
print(f"Excess Kurtosis: {kurt - 3:.4f}")