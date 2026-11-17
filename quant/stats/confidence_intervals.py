"""Confidence intervals for means and variances.

Two-sided intervals for a population mean (normal when the variance is known,
Student-t when estimated) and for a population variance (chi-squared).
Reference: Alexander (2008), Vol. I, Section I.3.4 (Example I.3.14).
"""

import numpy as np
import scipy.stats as stats


def normal_confidence_interval_mean(sample_mean, pop_std, n, confidence_level=0.95):
    """
    Calculates a two-sided confidence interval for a population mean
    when the population variance is KNOWN.
    """
    alpha = 1 - ((1 - confidence_level) / 2)
    z_critical = stats.norm.ppf(alpha)
    margin_of_error = z_critical * (pop_std / np.sqrt(n))
    return sample_mean - margin_of_error, sample_mean + margin_of_error


def student_t_confidence_interval_mean(sample_mean, sample_std, n, confidence_level=0.95):
    """
    Calculates a two-sided confidence interval for a population mean
    when the population variance is UNKNOWN (estimated from sample).
    """
    degrees_of_freedom = n - 1
    alpha = 1 - ((1 - confidence_level) / 2)
    t_critical = stats.t.ppf(alpha, df=degrees_of_freedom)
    margin_of_error = t_critical * (sample_std / np.sqrt(n))
    return sample_mean - margin_of_error, sample_mean + margin_of_error


def chi_squared_confidence_interval_variance(sample_var, n, confidence_level=0.95):
    """
    Calculates a two-sided confidence interval for a population variance
    using the Chi-squared distribution.
    """
    degrees_of_freedom = n - 1
    lower_alpha = (1 - confidence_level) / 2
    upper_alpha = 1 - lower_alpha

    chi2_lower = stats.chi2.ppf(lower_alpha, df=degrees_of_freedom)
    chi2_upper = stats.chi2.ppf(upper_alpha, df=degrees_of_freedom)

    numerator = degrees_of_freedom * sample_var
    return numerator / chi2_upper, numerator / chi2_lower


def compute(data, confidence=0.95, pop_std=None) -> dict:
    """Standard facade: confidence intervals for a data sample.

    Parameters:
    data: 1-D array-like of observations (at least 2).
    confidence (float): confidence level in (0, 1).
    pop_std (float, optional): known population standard deviation; when
    given, the normal interval is used instead of the Student-t interval.

    Returns:
    dict: {"n", "mean", "method", "mean_ci", "variance", "variance_ci"}.
    """
    arr = np.asarray(data, dtype=float).ravel()
    if arr.size < 2:
        raise ValueError("data must contain at least 2 observations")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in the open interval (0, 1)")

    n = int(arr.size)
    mean = float(np.mean(arr))
    variance = float(np.var(arr, ddof=1))

    if pop_std is not None:
        mean_ci = normal_confidence_interval_mean(mean, float(pop_std), n, confidence)
        method = "normal"
    else:
        mean_ci = student_t_confidence_interval_mean(mean, float(np.sqrt(variance)), n, confidence)
        method = "student_t"
    var_ci = chi_squared_confidence_interval_variance(variance, n, confidence)

    return {
        "n": n,
        "mean": mean,
        "confidence": float(confidence),
        "method": method,
        "mean_ci": [float(mean_ci[0]), float(mean_ci[1])],
        "variance": variance,
        "variance_ci": [float(var_ci[0]), float(var_ci[1])],
    }


if __name__ == "__main__":
    # Recreating Example I.3.14 (Confidence Interval for a Population Mean)
    print("Example I.3.14 - 99% CI for Mean:")
    lower, upper = student_t_confidence_interval_mean(
        sample_mean=8, sample_std=2, n=11, confidence_level=0.99
    )
    print(f"Lower Bound: {lower:.2f}, Upper Bound: {upper:.2f}")  # Expected: [6.09, 9.91]
