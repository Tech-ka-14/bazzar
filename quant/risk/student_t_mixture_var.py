"""VaR of a two-component Student-t mixture distribution.

Solves the standardized mixture CDF numerically for the alpha-quantile;
VaR is the negative of that quantile.
Reference: Alexander (2008), Market Risk Analysis IV, Example IV.2.22.
"""

import numpy as np
from scipy.optimize import brentq
from scipy.stats import t


def calculate_student_t_mixture_var(
    pi: float,
    mu_1: float,
    sigma_1: float,
    df_1: float,
    mu_2: float,
    sigma_2: float,
    df_2: float,
    alpha: float = 0.01,
) -> float:
    """
    Calculates VaR for a 2-component Student t Mixture Distribution
    using numerical root-finding on the standardized CDF.
    """

    def standardized_t_cdf(x, df):
        # Scale x to evaluate the raw Student t CDF (adjusting for variance = 1)
        scaled_x = x * np.sqrt(df / (df - 2.0))
        return t.cdf(scaled_x, df)

    def mixture_cdf_root(x):
        # G(x) - alpha = 0
        cdf_1 = standardized_t_cdf((x - mu_1) / sigma_1, df_1)
        cdf_2 = standardized_t_cdf((x - mu_2) / sigma_2, df_2)
        return (pi * cdf_1) + ((1 - pi) * cdf_2) - alpha

    # Define bracket [lower, upper]
    max_sigma = max(sigma_1, sigma_2)
    min_mu = min(mu_1, mu_2)

    lower_bound = min_mu - (15 * max_sigma)  # Wider net for fat tails
    upper_bound = max(mu_1, mu_2) + (15 * max_sigma)

    x_alpha = brentq(mixture_cdf_root, lower_bound, upper_bound)
    return -x_alpha


# Example IV.2.22: Comparison of Mixture VaR Estimates
# Note: Input parameters scaled down slightly in Example to represent 10-day inputs directly


def compute(
    pi: float,
    mu_1: float,
    sigma_1: float,
    df_1: float,
    mu_2: float,
    sigma_2: float,
    df_2: float,
    alpha: float = 0.01,
) -> dict:
    """Standard facade: Student-t mixture VaR as a JSON-serializable dict.

    Parameters:
    pi (float): Weight of the first mixture component in (0, 1).
    mu_1, sigma_1, df_1 (float): Mean, volatility (positive) and degrees
    of freedom (> 2) of component 1.
    mu_2, sigma_2, df_2 (float): Same for component 2.
    alpha (float): Tail probability in (0, 1), e.g. 0.01.

    Returns:
    dict: {"method", "alpha", "var"} with "var" the positive loss
    fraction.
    """
    if not 0.0 < pi < 1.0:
        raise ValueError("pi must be in the open interval (0, 1)")
    if sigma_1 <= 0 or sigma_2 <= 0:
        raise ValueError("sigma_1 and sigma_2 must be positive")
    if df_1 <= 2 or df_2 <= 2:
        raise ValueError("df_1 and df_2 must be greater than 2")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    var = calculate_student_t_mixture_var(
        float(pi),
        float(mu_1),
        float(sigma_1),
        float(df_1),
        float(mu_2),
        float(sigma_2),
        float(df_2),
        float(alpha),
    )
    return {"method": "student_t_mixture", "alpha": float(alpha), "var": float(var)}


if __name__ == "__main__":
    pi_1 = 0.75
    mu_1_10d, vol_1_10d = 0.0, 0.20 * np.sqrt(10 / 250)
    mu_2_10d, vol_2_10d = -0.10 * (10 / 250), 0.40 * np.sqrt(10 / 250)

    df_component_1 = 10
    df_component_2 = 5

    t_mix_var = calculate_student_t_mixture_var(
        pi_1, mu_1_10d, vol_1_10d, df_component_1, mu_2_10d, vol_2_10d, df_component_2, alpha=0.01
    )

    print(f"1% 10-day Student t Mixture VaR: {t_mix_var:.2%}")
