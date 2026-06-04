import numpy as np

def calculate_empirical_etl(historical_returns: np.ndarray, var_percentage: float) -> float:
    """
    Calculates the Empirical Expected Tail Loss (ETL) from a historical returns distribution.
    
    Parameters:
    historical_returns (np.ndarray): Array of historically simulated portfolio returns.
    var_percentage (float): The previously calculated VaR (expressed as a positive loss percentage).
    
    Returns:
    float: The Empirical ETL (expressed as a positive loss percentage).
    """
    # Isolate the returns that represent losses strictly worse than the VaR threshold
    tail_losses = historical_returns[historical_returns < -var_percentage]
    
    if len(tail_losses) == 0:
        return var_percentage # Fallback if no returns breach the threshold
        
    # ETL is the expected (average) severity of these extreme losses
    empirical_etl = -np.mean(tail_losses)
    
    return empirical_etl

# Conceptual Demonstration
np.random.seed(42)
mock_returns = np.random.normal(0.001, 0.02, 5000)

# Assuming we already found the 1% VaR
var_1_pct = 0.0455 # 4.55% VaR

emp_etl = calculate_empirical_etl(mock_returns, var_1_pct)
print(f"Empirical 1% VaR: {var_1_pct:.2%}")
print(f"Empirical 1% Expected Tail Loss (ETL): {emp_etl:.2%}")