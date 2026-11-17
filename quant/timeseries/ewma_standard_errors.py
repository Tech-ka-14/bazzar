"""Standard errors and precision of EWMA variance forecasts.

Asymptotic standard error sqrt((1 - lambda) / (1 + lambda)) of an EWMA
variance estimator, and the corresponding lower/upper confidence bounds for
the variance forecast.
"""

import numpy as np


def ewma_variance_confidence(lambda_param, variance_forecast, alpha=0.05):
    """
    Calculates the asymptotic standard error and confidence bounds for
    an EWMA variance forecast.
    """
    # Calculate the asymptotic standard error (ASE)
    ase = np.sqrt((1 - lambda_param) / (1 + lambda_param))

    # Z-score for the given alpha (e.g., 1.96 for 95% confidence)
    from scipy.stats import norm

    z_score = norm.ppf(1 - alpha / 2)

    # Calculate bounds
    lower_bound = variance_forecast * (1 - (z_score * ase))
    upper_bound = variance_forecast * (1 + (z_score * ase))

    return {
        "lambda": lambda_param,
        "Asymptotic_Std_Error": ase,
        "Lower_Bound": lower_bound,
        "Upper_Bound": upper_bound,
    }


def compute(data, variance_forecast=None, alpha: float = 0.05) -> dict:
    """Standard facade: EWMA variance confidence bounds as a JSON dict.

    Parameters:
    data (float): EWMA smoothing constant lambda in (0, 1).
    variance_forecast (float): the EWMA variance forecast (non-negative).
    alpha (float): two-sided test size in (0, 1), e.g. 0.05 for 95% bounds.

    Returns:
    dict: {"lambda", "asymptotic_std_error", "z_score", "lower_bound",
    "upper_bound"} with plain floats.
    """
    lambda_param = float(data)
    if not 0.0 < lambda_param < 1.0:
        raise ValueError("lambda must be in the open interval (0, 1)")
    if variance_forecast is None:
        raise ValueError("variance_forecast is required")
    variance_forecast = float(variance_forecast)
    if variance_forecast < 0.0:
        raise ValueError("variance_forecast must be non-negative")
    if not 0.0 < float(alpha) < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    from scipy.stats import norm

    result = ewma_variance_confidence(lambda_param, variance_forecast, float(alpha))
    z_score = float(norm.ppf(1 - float(alpha) / 2))
    return {
        "lambda": lambda_param,
        "asymptotic_std_error": float(result["Asymptotic_Std_Error"]),
        "z_score": z_score,
        "lower_bound": float(result["Lower_Bound"]),
        "upper_bound": float(result["Upper_Bound"]),
    }


if __name__ == "__main__":
    # Example implementation based on the text's S&P 500 analogy
    # Current volatility of 15% -> Variance = 0.15^2 = 0.0225
    current_variance = 0.0225

    # Test different lambdas as mentioned in the text (0.90, 0.95, 0.99)
    for lam in [0.90, 0.95, 0.99]:
        result = ewma_variance_confidence(lam, current_variance)
        print(
            f"Lambda: {result['lambda']} | ASE: {result['Asymptotic_Std_Error']:.4f} | "
            f"95% CI: [{result['Lower_Bound']:.4f}, {result['Upper_Bound']:.4f}]"
        )
