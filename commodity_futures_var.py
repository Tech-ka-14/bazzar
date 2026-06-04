import numpy as np
from scipy.stats import norm

def calculate_commodity_position_vector(contracts: list, prices: list, multiplier: float) -> np.ndarray:
    """
    Calculates the nominal dollar exposure vector (theta) for commodity futures.
    """
    return np.array(contracts) * np.array(prices) * multiplier

def calculate_commodity_desk_var(theta: np.ndarray, omega_1: np.ndarray, 
                                 horizon_days: int = 10, alpha: float = 0.01):
    """
    Calculates the Stand-Alone VaR for a single commodity desk.
    """
    variance_1d = theta.T @ omega_1 @ theta
    volatility_h = np.sqrt(variance_1d) * np.sqrt(horizon_days)
    
    critical_value = norm.ppf(1 - alpha)
    return critical_value * volatility_h

def calculate_desk_marginal_var(theta_total: np.ndarray, omega_total_1d: np.ndarray, 
                                split_index: int, horizon_days: int = 10, alpha: float = 0.01):
    """
    Calculates the Marginal VaR contribution of each desk using the DelVaR gradient.
    """
    variance_1d = theta_total.T @ omega_total_1d @ theta_total
    volatility_1d = np.sqrt(variance_1d)
    
    z_score = norm.ppf(1 - alpha)
    
    # Gradient vector (DelVaR) scaled to h-days
    gradient_1d = (omega_total_1d @ theta_total) / volatility_1d
    gradient_h = gradient_1d * np.sqrt(horizon_days) * z_score
    
    # Element-wise marginal contributions
    marginal_components = theta_total * gradient_h
    
    # Sum components by desk
    desk_1_marginal = np.sum(marginal_components[:split_index])
    desk_2_marginal = np.sum(marginal_components[split_index:])
    total_var = desk_1_marginal + desk_2_marginal
    
    return total_var, desk_1_marginal, desk_2_marginal


# --- Executing Case Study IV.2.7 Data ---

# 1. Position Setup (Table IV.2.19)
gas_multiplier = 10_000
gas_prices = [7.67, 7.66, 7.69, 7.70, 7.84]
gas_contracts = [-75, -30, -10, 15, 25]

silver_multiplier = 5_000
silver_prices = [13.50, 13.39, 13.62, 13.62, 13.56]
silver_contracts = [100, 50, 20, -50, -100]

theta_gas = calculate_commodity_position_vector(gas_contracts, gas_prices, gas_multiplier)
theta_silver = calculate_commodity_position_vector(silver_contracts, silver_prices, silver_multiplier)

print(f"Total Nominal Exposure (Gas): ${np.sum(np.abs(theta_gas)):,.0f}")
print(f"Total Nominal Exposure (Silver): ${np.sum(np.abs(theta_silver)):,.0f}\n")

# 2. Mock 1-Day Covariance Matrices (In reality, derived from historical returns in Table IV.2.18)
# We generate mock matrices structured to yield similar sub-additive results to Table IV.2.20
np.random.seed(42)

# Gas Covariance (High Volatility)
vols_gas = np.array([0.587, 0.550, 0.498, 0.458, 0.418]) / np.sqrt(250)
corr_gas = np.ones((5, 5)) * 0.90 + np.eye(5) * 0.10
omega_gas_1d = np.outer(vols_gas, vols_gas) * corr_gas

# Silver Covariance (Medium Volatility)
vols_sil = np.array([0.441, 0.439, 0.427, 0.433, 0.404]) / np.sqrt(250)
corr_sil = np.ones((5, 5)) * 0.88 + np.eye(5) * 0.12
omega_sil_1d = np.outer(vols_sil, vols_sil) * corr_sil

# 3. Calculate Stand-Alone VaR
gas_standalone_var = calculate_commodity_desk_var(theta_gas, omega_gas_1d)
silver_standalone_var = calculate_commodity_desk_var(theta_silver, omega_sil_1d)

print(f"Stand-Alone Gas VaR: ${gas_standalone_var:,.0f}")
print(f"Stand-Alone Silver VaR: ${silver_standalone_var:,.0f}")
print(f"Sum of Stand-Alone VaRs: ${gas_standalone_var + silver_standalone_var:,.0f}\n")

# 4. Aggregated Total VaR and Marginal VaR (Assuming 20% cross-correlation between Gas and Silver)
cross_corr = 0.20
omega_cross = np.outer(vols_gas, vols_sil) * cross_corr

omega_total_1d = np.block([
    [omega_gas_1d, omega_cross],
    [omega_cross.T, omega_sil_1d]
])

theta_total = np.concatenate([theta_gas, theta_silver])

total_var, gas_marginal, silver_marginal = calculate_desk_marginal_var(
    theta_total, omega_total_1d, split_index=5
)

print(f"Total Aggregated VaR: ${total_var:,.0f}")
print(f"Marginal Contribution - Gas: ${gas_marginal:,.0f} ({gas_marginal/total_var:.1%})")
print(f"Marginal Contribution - Silver: ${silver_marginal:,.0f} ({silver_marginal/total_var:.1%})")