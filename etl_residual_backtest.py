import numpy as np

def calculate_etl_exceedance_residuals(returns: np.ndarray, 
                                       var_forecasts: np.ndarray, 
                                       etl_forecasts: np.ndarray, 
                                       volatility_forecasts: np.ndarray) -> np.ndarray:
    """
    Isolates days where losses exceed VaR and calculates the 
    Standardized Exceedance Residuals (SER).
    """
    # Find indices where realized loss exceeds the forecasted VaR
    # Note: Assuming returns are standard percentages (e.g., -0.05 is a 5% loss)
    # and VaR is expressed as a positive percentage (e.g., 0.03 for 3% VaR)
    exceedance_mask = returns < -var_forecasts
    
    # Isolate the data for exceedance days
    y_exceed = returns[exceedance_mask]
    etl_exceed = etl_forecasts[exceedance_mask]
    vol_exceed = volatility_forecasts[exceedance_mask]
    
    # Calculate SER
    ser = (-y_exceed - etl_exceed) / vol_exceed
    return ser

def etl_mean_residual_test(ser: np.ndarray) -> tuple:
    """
    Calculates the pseudo t-statistic for the ETL residuals.
    """
    mean_ser = np.mean(ser)
    std_ser = np.std(ser, ddof=1)
    n_exceedances = len(ser)
    
    standard_error = std_ser / np.sqrt(n_exceedances)
    t_stat = mean_ser / standard_error
    
    return mean_ser, t_stat