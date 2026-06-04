import pandas as pd
from statsmodels.tsa.api import VAR

def fit_var_model(stationary_returns, max_lags=5):
    """
    Fits a Vector Autoregression (VAR) model to a DataFrame of stationary returns
    and determines the optimal lag length using the Akaike Information Criterion (AIC).
    """
    # Initialize the VAR model
    model = VAR(stationary_returns)
    
    # Fit the model, allowing statsmodels to select the optimal lag up to max_lags
    fitted_var = model.fit(maxlags=max_lags, ic='aic')
    
    # Extract the optimal lag order chosen by the AIC
    optimal_lag = fitted_var.k_ar
    
    return {
        "Optimal Lags (p)": optimal_lag,
        "Coefficient Matrices (Phi)": fitted_var.coefs,
        "Intercepts (Alpha)": fitted_var.intercept,
        "Residual Covariance": fitted_var.sigma_u,
        "Model Summary": fitted_var.summary()
    }

# Example Usage:
# Assuming 'portfolio_returns' is a strictly stationary Pandas DataFrame of asset returns
# var_results = fit_var_model(portfolio_returns, max_lags=10)