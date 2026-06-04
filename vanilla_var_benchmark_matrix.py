import numpy as np
import pandas as pd
from scipy.stats import norm

def generate_var_benchmark_matrix(volatilities: list, alphas: list, horizons: list):
    """
    Generates Table IV.2.1: Normal linear VaR for different volatilities, 
    significance levels, and risk horizons.
    """
    # Create MultiIndex for columns (Alpha Level -> Risk Horizon)
    columns = pd.MultiIndex.from_product(
        [[f"{a*100:g}%" for a in alphas], [f"{h}-day" for h in horizons]],
        names=['Significance (\u03B1)', 'Horizon (h)']
    )
    
    # Initialize an empty DataFrame
    df_var = pd.DataFrame(index=[f"{v*100:g}%" for v in volatilities], columns=columns)
    df_var.index.name = "Daily Volatility"
    
    # Populate the matrix
    for vol in volatilities:
        row_label = f"{vol*100:g}%"
        for alpha in alphas:
            alpha_label = f"{alpha*100:g}%"
            critical_value = norm.ppf(1 - alpha)
            
            for h in horizons:
                horizon_label = f"{h}-day"
                # Equation IV.2.6 & IV.2.7: Square-root-of-time scaling
                var_estimate = critical_value * vol * np.sqrt(h)
                
                # Format as percentage string
                df_var.loc[row_label, (alpha_label, horizon_label)] = f"{var_estimate:.1%}"
                
    return df_var

# Define the parameters from Table IV.2.1
volatilities = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1.00]
alphas = [0.001, 0.01, 0.05, 0.10]
horizons = [10, 1]

# Generate and display the matrix
var_matrix = generate_var_benchmark_matrix(volatilities, alphas, horizons)

print("Table IV.2.1 Normal linear VaR Benchmark Matrix")
print("-" * 80)
print(var_matrix.to_string())
print("-" * 80)