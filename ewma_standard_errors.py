import numpy as np
import pandas as pd

def ewma_precision_metrics(lambda_param):
    """
    Calculates the estimated standard error for EWMA variance and volatility forecasts 
    (expressed as a percentage of the forecast) for a given lambda.
    """
    # Variance Standard Error (%)
    var_pct_se = np.sqrt(2 * ((1 - lambda_param) / (1 + lambda_param)))
    
    # Volatility Standard Error (%)
    vol_pct_se = np.sqrt((1 - lambda_param) / (2 * (1 + lambda_param)))
    
    return {
        "Lambda": lambda_param,
        "Variance Std Error (%)": var_pct_se * 100,
        "Volatility Std Error (%)": vol_pct_se * 100
    }

# Example replicating Figure II.3.8 from the text
lambdas = [0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.98]
errors = pd.DataFrame([ewma_precision_metrics(l) for l in lambdas])
print(errors)