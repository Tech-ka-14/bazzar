"""Critical values of common test distributions.

Percent points (inverse CDF) of the standard normal, Student-t and
chi-squared distributions. Reference: Alexander (2008), Vol. I,
Examples I.3.13-I.3.14.
"""

import scipy.stats as stats


def get_normal_critical_value(alpha):
    """
    Calculates the critical value for a Standard Normal distribution.
    Matches the text's inverse standard normal function phi^-1(alpha).
    """
    return stats.norm.ppf(alpha)


def get_student_t_critical_value(alpha, degrees_of_freedom):
    """
    Calculates the critical value for a Student t distribution.
    Replaces the text's complex Excel TINV workaround.
    """
    return stats.t.ppf(alpha, df=degrees_of_freedom)


def get_chi_squared_critical_value(alpha, degrees_of_freedom):
    """
    Calculates the critical value for a Chi-squared distribution.
    """
    return stats.chi2.ppf(alpha, df=degrees_of_freedom)


def compute(alpha, degrees_of_freedom=None) -> dict:
    """Standard facade: critical values at tail probability alpha.

    Parameters:
    alpha (float): cumulative probability in (0, 1), e.g. 0.975.
    degrees_of_freedom (int, optional): when given, Student-t and
    chi-squared critical values are included.

    Returns:
    dict: {"alpha", "normal"} plus {"student_t", "chi_squared"} when
    degrees_of_freedom is provided.
    """
    alpha = float(alpha)
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    out = {"alpha": alpha, "normal": float(get_normal_critical_value(alpha))}
    if degrees_of_freedom is not None:
        df = int(degrees_of_freedom)
        if df < 1:
            raise ValueError("degrees_of_freedom must be a positive integer")
        out["student_t"] = float(get_student_t_critical_value(alpha, df))
        out["chi_squared"] = float(get_chi_squared_critical_value(alpha, df))
    return out


if __name__ == "__main__":
    # Example I.3.13 / I.3.14 Recreations:
    print(
        f"Normal 97.5% Critical Value: {get_normal_critical_value(0.975):.4f}"
    )  # Expected: 1.9600
    print(
        f"Student t 99.5% Critical Value (df=10): {get_student_t_critical_value(0.995, 10):.4f}"
    )  # Expected: 3.1693
