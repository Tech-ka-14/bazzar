import numpy as np

def adjusted_volatility_scaling(daily_vol, h, rho):
    """
    Adjusts the volatility forecast for an h-period horizon when returns 
    exhibit first-order autocorrelation (rho).
    
    Parameters:
    daily_vol (float): Daily volatility (sigma_1).
    h (int): Number of periods to forecast (e.g., 5 days, 22 days).
    rho (float): First-order autocorrelation coefficient.
    
    Returns:
    float: The adjusted h-period volatility.
    """
    # The variance scaling factor (h + 2 * sum(1 - j/h) * rho^j)
    # Simplified for first-order autocorrelation:
    # Var_h = Var_1 * [ h + 2 * rho * (h - (1 - rho^h)/(1 - rho)) / (1 - rho) ]
    
    # Calculate the variance multiplier (the term inside the square root)
    if rho == 0:
        multiplier = h
    else:
        # Summation formula for first-order autocorrelation
        multiplier = h + (2 * rho / (1 - rho)) * (h - (1 - rho**h) / (1 - rho))
    
    adjusted_vol = daily_vol * np.sqrt(multiplier)
    return adjusted_vol

if __name__ == "__main__":
    # --- Example Application ---
    # Daily vol 1.5%, 10-day forecast, 10% positive serial correlation
    sigma_1 = 0.015
    h_days = 10
    rho_1 = 0.10
    
    # Standard Square-Root-of-Time
    standard_vol = sigma_1 * np.sqrt(h_days)
    
    # Adjusted
    adj_vol = adjusted_volatility_scaling(sigma_1, h_days, rho_1)
    
    print("--- Volatility Scaling Adjustment ---")
    print(f"Standard Forecast (i.i.d.): {standard_vol * 100:.2f}%")
    print(f"Adjusted Forecast (Autocorrelated): {adj_vol * 100:.2f}%")