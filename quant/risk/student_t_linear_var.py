"""Student-t linear VaR over an h-day horizon.

Uses the standardized Student-t critical value (unit variance scaling)
with square-root-of-time volatility scaling and linear mean scaling.
Reference: Alexander (2008), Market Risk Analysis IV, Equation IV.2.63,
Examples IV.2.18-IV.2.19.
"""

import numpy as np
from scipy.stats import norm, t


def calculate_student_t_var(
    mu: float, sigma: float, df: float, alpha: float = 0.01, h_days: int = 1
):
    """
    Calculates the generalized Student t Linear VaR over an h-day horizon.
    Equation IV.2.63.

    Parameters:
    mu (float): 1-day expected excess return.
    sigma (float): 1-day standard deviation (volatility).
    df (float): Degrees of freedom (nu). Must be > 2 for variance to be defined.
    alpha (float): Significance level.
    h_days (int): Risk horizon in days.
    """
    if df <= 2:
        raise ValueError(
            "Degrees of freedom (nu) must be greater than 2 to have a defined variance."
        )

    # 1. Calculate the raw critical value from the standard Student t distribution
    t_critical = t.ppf(1 - alpha, df)

    # 2. Calculate the variance standardization factor: sqrt((nu - 2) / nu)
    standardization_factor = np.sqrt((df - 2) / df)

    # 3. Apply the time scaling: sqrt(h)
    time_scale = np.sqrt(h_days)

    # 4. Calculate VaR (Eq IV.2.63)
    t_var = (standardization_factor * time_scale * t_critical * sigma) - (h_days * mu)

    return t_var


# Example IV.2.18 & IV.2.19: Comparison of Normal and Student t VaR (FTSE 100)
# Assuming typical daily volatility of ~1.08% to match the text's 1-day 1% VaR outputs


def compute(mu: float, sigma: float, df: float, alpha: float = 0.01, h_days: int = 1) -> dict:
    """Standard facade: Student-t linear VaR as a JSON-serializable dict.

    Parameters:
    mu (float): 1-day expected excess return (fraction).
    sigma (float): 1-day volatility (positive).
    df (float): Degrees of freedom, must be > 2.
    alpha (float): Tail probability in (0, 1), e.g. 0.01.
    h_days (int): Risk horizon in days (>= 1).

    Returns:
    dict: {"method", "alpha", "h_days", "df", "var"} with "var" the
    positive loss fraction.
    """
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    if df <= 2:
        raise ValueError("df must be greater than 2 for a defined variance")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    var = calculate_student_t_var(float(mu), float(sigma), float(df), float(alpha), int(h_days))
    return {
        "method": "student_t_linear",
        "alpha": float(alpha),
        "h_days": int(h_days),
        "df": float(df),
        "var": float(var),
    }


if __name__ == "__main__":
    daily_vol = 0.0108
    daily_mu = 0.0
    degrees_of_freedom_mle = 4.14

    # Compare at 0.1%, 1%, and 10% significance levels
    alphas = [0.001, 0.01, 0.10]

    print("--- 1-Day VaR Comparison (Normal vs. Student t) ---")
    for a in alphas:
        # Normal VaR
        norm_var = (norm.ppf(1 - a) * daily_vol) - daily_mu

        # Student t VaR
        t_var = calculate_student_t_var(
            daily_mu, daily_vol, degrees_of_freedom_mle, alpha=a, h_days=1
        )

        print(f"Significance {a:.1%}: Normal VaR = {norm_var:.2%} | Student t VaR = {t_var:.2%}")
