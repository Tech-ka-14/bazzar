import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint

def engle_granger_ecm(series_y, series_x):
    """
    Performs the Engle-Granger two-step cointegration test and 
    estimates the Error Correction Model (ECM).
    """
    # STEP 1 & 2: Cointegration Test
    # The 'coint' function natively handles the regression and ADF test on residuals
    coint_t_stat, p_value, crit_values = coint(series_y, series_x)
    is_cointegrated = p_value < 0.05
    
    if not is_cointegrated:
        return {"Cointegrated": False, "p-value": p_value}
    
    # STEP 3: Build the Error Correction Model (ECM)
    # Regress Y on X to get the residuals (the spread/error term)
    X_const = sm.add_constant(series_x)
    coint_model = sm.OLS(series_y, X_const).fit()
    residuals = coint_model.resid
    
    # Calculate differences (delta Y and delta X)
    delta_Y = series_y.diff().dropna()
    delta_X = series_x.diff().dropna()
    
    # Lagged residuals (error correction term)
    lagged_residuals = residuals.shift(1).dropna()
    
    # Align indices after differencing and shifting
    aligned_data = pd.DataFrame({
        'dY': delta_Y,
        'dX': delta_X,
        'ECM_Term': lagged_residuals
    }).dropna()
    
    # ECM Regression: dY_t = gamma_0 + gamma_1*dX_t + lambda*ECM_t-1 + u_t
    X_ecm = sm.add_constant(aligned_data[['dX', 'ECM_Term']])
    ecm_model = sm.OLS(aligned_data['dY'], X_ecm).fit()
    
    # The coefficient of the ECM_Term is lambda (speed of adjustment)
    lambda_param = ecm_model.params['ECM_Term']
    
    return {
        "Cointegrated": True,
        "Cointegration p-value": p_value,
        "Spread Beta (Long-term multiplier)": coint_model.params[series_x.name],
        "Speed of Adjustment (Lambda)": lambda_param,
        "ECM Summary": ecm_model.summary().tables[1]
    }

# Example usage (assuming price_A and price_B are non-stationary series)
# ecm_results = engle_granger_ecm(series_y=price_A, series_x=price_B)