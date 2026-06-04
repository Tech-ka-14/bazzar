import numpy as np
import scipy.stats as stats

def normal_scenario_var_etl(mu: float, sigma: float, alpha: float) -> tuple:
    """
    Calculates univariate Scenario VaR and ETL assuming a normal distribution 
    of uncertainty around the expected return.
    """
    z_score = stats.norm.ppf(1 - alpha)
    var = (z_score * sigma) - mu
    
    # Normal ETL analytical formula
    pdf_val = stats.norm.pdf(stats.norm.ppf(alpha))
    etl = (pdf_val / alpha) * sigma - mu
    return var, etl

def multivariate_scenario_var(exposures: np.ndarray, expected_changes: np.ndarray, 
                              covariance_matrix: np.ndarray, alpha: float) -> float:
    """
    Calculates multivariate normal scenario VaR given an exposure vector (theta),
    expected changes (mu), and uncertainty covariance (Omega).
    """
    z_score = stats.norm.ppf(1 - alpha)
    
    # Portfolio variance: theta' * Omega * theta
    portfolio_variance = exposures.T @ covariance_matrix @ exposures
    portfolio_volatility = np.sqrt(portfolio_variance)
    
    # Expected portfolio change: theta' * mu
    expected_portfolio_change = exposures.T @ expected_changes
    
    var = (z_score * portfolio_volatility) - expected_portfolio_change
    return var