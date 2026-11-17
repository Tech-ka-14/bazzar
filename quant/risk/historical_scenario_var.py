"""Scenario VaR for a hypothetical crisis distribution.

Normal scenario VaR and Cornish-Fisher scenario VaR (accounting for the
skewness and excess kurtosis of the crisis scenario).
Reference: Alexander (2008), Market Risk Analysis IV, Example IV.7.1.
"""

import scipy.stats as stats


def calculate_normal_scenario_var(mean: float, std_dev: float, alpha: float) -> float:
    """
    Calculates the Scenario VaR assuming the crisis distribution is Normal.
    """
    z_score = stats.norm.ppf(1 - alpha)
    # VaR is typically expressed as a positive loss percentage
    var = (z_score * std_dev) - mean
    return var


def calculate_cornish_fisher_scenario_var(
    mean: float, std_dev: float, skewness: float, excess_kurtosis: float, alpha: float
) -> float:
    """
    Calculates the Scenario VaR using a Cornish-Fisher expansion to account
    for the extreme skewness and kurtosis present in the crisis scenario.
    """
    z = stats.norm.ppf(1 - alpha)

    # Cornish-Fisher expansion adjustment
    z_cf = (
        z
        + (1 / 6) * (z**2 - 1) * skewness
        + (1 / 24) * (z**3 - 3 * z) * excess_kurtosis
        - (1 / 36) * (2 * z**3 - 5 * z) * (skewness**2)
    )

    var = (z_cf * std_dev) - mean
    return var


# Example IV.7.1: 1987 Global Equity Crash Scenario


def compute(
    mean, std_dev, skewness: float = 0.0, excess_kurtosis: float = 0.0, alpha: float = 0.01
) -> dict:
    """Standard facade: normal and Cornish-Fisher scenario VaR as a JSON dict.

    Parameters:
    mean, std_dev (float): Mean and volatility of the crisis scenario
    return distribution (std_dev > 0).
    skewness, excess_kurtosis (float): Higher moments of the scenario.
    alpha (float): Tail probability in (0, 1), e.g. 0.01.

    Returns:
    dict: {"method", "alpha", "var_normal", "var_cornish_fisher"} with
    positive loss fractions.
    """
    if std_dev <= 0:
        raise ValueError("std_dev must be positive")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    var_normal = calculate_normal_scenario_var(float(mean), float(std_dev), float(alpha))
    var_cf = calculate_cornish_fisher_scenario_var(
        float(mean), float(std_dev), float(skewness), float(excess_kurtosis), float(alpha)
    )
    return {
        "method": "scenario",
        "alpha": float(alpha),
        "var_normal": float(var_normal),
        "var_cornish_fisher": float(var_cf),
    }


if __name__ == "__main__":
    crash_mean = -0.0121  # -1.21%
    crash_std = 0.0394  # 3.94%
    crash_skew = -0.3202
    crash_kurt = 1.6139

    # 99% Confidence (alpha = 0.01)
    normal_var_99 = calculate_normal_scenario_var(crash_mean, crash_std, 0.01)
    cf_var_99 = calculate_cornish_fisher_scenario_var(
        crash_mean, crash_std, crash_skew, crash_kurt, 0.01
    )
