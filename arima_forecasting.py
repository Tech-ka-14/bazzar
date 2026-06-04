import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import warnings
warnings.filterwarnings("ignore") # Ignore convergence warnings for simplicity

def fit_and_forecast_arima(time_series, order=(1, 1, 1), steps_ahead=5):
    """
    Fits an ARIMA(p,d,q) model to the data and generates out-of-sample forecasts.
    order: A tuple of (p, d, q)
    """
    # Initialize and fit the ARIMA model
    model = ARIMA(time_series, order=order)
    fitted_model = model.fit()
    
    # Generate forecast
    forecast = fitted_model.forecast(steps=steps_ahead)
    
    # Extract model summary metrics
    aic = fitted_model.aic
    bic = fitted_model.bic
    
    return {
        "Model Summary": fitted_model.summary().tables[1],
        "AIC": aic,
        "BIC": bic,
        "Forecast": forecast
    }

# Example usage
# arima_results = fit_and_forecast_arima(prices, order=(2, 1, 1), steps_ahead=10)