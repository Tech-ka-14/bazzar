"""Impulse response analysis for VAR models.

Traces the response of each variable to a one-standard-deviation shock in
each innovation over a number of periods, using a fitted VAR model.
"""

from statsmodels.tsa.api import VAR


def analyze_impulse_response(stationary_returns, periods=10):
    """
    Fits a VAR model and calculates the Impulse Response Functions (IRF).
    """
    model = VAR(stationary_returns)
    fitted_var = model.fit(maxlags=5, ic="aic")

    # Calculate the Impulse Response Functions
    irf = fitted_var.irf(periods)

    # Note: We do not call irf.plot() here, as we cannot display plots in this console output.
    # We return the IRF object containing the numerical responses.
    return irf


def compute(data, periods: int = 10) -> dict:
    """Standard facade: orthogonalized impulse responses as a JSON dict.

    Parameters:
    data: 2-D array-like (T observations x k variables) or pandas DataFrame
    of stationary returns.
    periods (int): Number of response periods to compute (>= 1).

    Returns:
    dict: {"periods", "n_variables", "orth_irfs"} where orth_irfs is the
    (periods + 1) x k x k array of orthogonalized impulse responses
    (row = horizon, column = responding variable, depth = impulse).
    """
    periods = int(periods)
    if periods < 1:
        raise ValueError("periods must be at least 1")

    irf = analyze_impulse_response(data, periods=periods)
    orth = irf.orth_irfs
    return {
        "periods": periods,
        "n_variables": int(orth.shape[-1]),
        "orth_irfs": orth.tolist(),
    }


# Example usage
# irf_results = analyze_impulse_response(portfolio_returns, periods=10)
# print("Shape of IRF matrix:", irf_results.orth_irfs.shape)
