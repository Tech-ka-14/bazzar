import pandas as pd
from statsmodels.tsa.api import VAR

def generate_impulse_response(stationary_returns, steps=10):
    """
    Fits a VAR model and generates the Orthogonalized Impulse Response Function (IRF)
    to trace how shocks propagate through the portfolio.
    """
    # Fit the VAR model (defaulting to AIC optimal lag selection)
    model = VAR(stationary_returns)
    fitted_var = model.fit(ic='aic')
    
    # Generate the Orthogonalized Impulse Response Function
    # 'steps' defines how many forward periods the shock is traced
    irf = fitted_var.irf(steps)
    
    # Extract the orthogonalized IRF arrays
    # Shape: (steps+1, n_variables, n_variables)
    # Interpretation: irf_matrix[s, i, j] is the effect on variable i from a shock to variable j at step s
    orth_irf_matrices = irf.orth_irfs
    
    return {
        "IRF Matrices": orth_irf_matrices,
        "Cumulative IRF Matrices": irf.cum_effects,
        "IRF Object": irf  # Can be used directly for plotting: irf.plot()
    }

# Example Usage:
# irf_results = generate_impulse_response(portfolio_returns, steps=5)