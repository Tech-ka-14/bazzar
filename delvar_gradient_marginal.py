import numpy as np
from scipy.stats import norm

def calculate_delvar_gradient(theta: np.ndarray, omega_h: np.ndarray, alpha: float = 0.01) -> np.ndarray:
    """
    Calculates the gradient vector (DelVaR) of the normal linear VaR.
    Equation IV.2.24.
    """
    critical_value = norm.ppf(1 - alpha)
    
    # Calculate portfolio variance and volatility
    variance = theta.T @ omega_h @ theta
    volatility = np.sqrt(variance)
    
    # Calculate the gradient: Z * (Omega * theta) * (1 / volatility)
    gradient = critical_value * (omega_h @ theta) * (1.0 / volatility)
    
    return gradient

def calculate_marginal_and_incremental_var(theta: np.ndarray, delta_theta: np.ndarray, 
                                           omega_h: np.ndarray, alpha: float = 0.01):
    """
    Calculates Marginal VaR components and Incremental VaR using the DelVaR gradient.
    Equations IV.2.22 and IV.2.23.
    """
    # 1. Get the gradient vector
    gradient = calculate_delvar_gradient(theta, omega_h, alpha)
    
    # 2. Marginal VaR components: Element-wise multiplication of theta and gradient
    marginal_var_components = theta * gradient
    
    # 3. Incremental VaR for a specific trade (delta_theta)
    incremental_var = delta_theta.T @ gradient
    
    return marginal_var_components, incremental_var

# Example Usage
theta_initial = np.array([100.0, 50.0]) # Initial positions
trade_vector = np.array([10.0, -5.0])   # Buying 10 of asset 1, selling 5 of asset 2
omega = np.array([
    [0.04, 0.02],
    [0.02, 0.09]
])

marginals, incremental = calculate_marginal_and_incremental_var(theta_initial, trade_vector, omega)

print(f"Marginal VaR Vector: {marginals}")
print(f"Sum of Marginals (Total VaR): {np.sum(marginals):.4f}")
print(f"Estimated Incremental VaR from Trade: {incremental:.4f}")