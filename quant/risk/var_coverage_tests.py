"""VaR coverage backtests: Kupiec unconditional coverage and Christoffersen
independence.

Kupiec (1995) tests whether the observed exceedance rate matches the VaR
tail probability alpha; Christoffersen (1998) tests the independence of
exceedances via a first-order Markov transition matrix. Both statistics are
asymptotically chi-squared with 1 degree of freedom (their sum, the
conditional coverage statistic, has 2).
"""

import numpy as np
import scipy.stats as stats


def kupiec_unconditional_coverage(n_obs: int, n_exceedances: int, alpha: float) -> tuple:
    """
    Calculates the Kupiec Unconditional Coverage test statistic.
    """
    pi_exp = alpha
    pi_obs = n_exceedances / n_obs
    n0 = n_obs - n_exceedances
    n1 = n_exceedances

    # Handle the edge case of 0 exceedances to avoid log(0)
    if n1 == 0:
        log_lr_uc = n0 * np.log(1 - pi_exp) - n0 * np.log(1 - pi_obs)
    else:
        log_lr_uc = (n1 * np.log(pi_exp) + n0 * np.log(1 - pi_exp)) - (
            n1 * np.log(pi_obs) + n0 * np.log(1 - pi_obs)
        )

    test_statistic = -2 * log_lr_uc
    p_value = 1 - stats.chi2.cdf(test_statistic, df=1)
    return test_statistic, p_value


def christoffersen_independence(n00: int, n01: int, n10: int, n11: int) -> tuple:
    """
    Calculates the Christoffersen Independence test statistic based on Markov transitions.
    """
    n0 = n00 + n10
    n1 = n01 + n11
    pi_obs = n1 / (n0 + n1)

    pi_01 = n01 / (n00 + n01) if (n00 + n01) > 0 else 0
    pi_11 = n11 / (n10 + n11) if (n10 + n11) > 0 else 0

    # Numerator Log-Likelihood (assuming independence)
    ll_null = n1 * np.log(pi_obs) + n0 * np.log(1 - pi_obs)

    # Denominator Log-Likelihood (assuming Markov dependence)
    # Using np.log with a small floor to prevent log(0) errors
    ll_alt = 0
    if n00 > 0:
        ll_alt += n00 * np.log(1 - pi_01)
    if n01 > 0:
        ll_alt += n01 * np.log(pi_01)
    if n10 > 0:
        ll_alt += n10 * np.log(1 - pi_11)
    if n11 > 0:
        ll_alt += n11 * np.log(pi_11)

    test_statistic = -2 * (ll_null - ll_alt)
    p_value = 1 - stats.chi2.cdf(test_statistic, df=1)
    return test_statistic, p_value


def compute(n_obs: int, n_exceedances: int, confidence: float, transitions=None) -> dict:
    """Standard facade: VaR coverage backtests as a JSON-serializable dict.

    Parameters:
    n_obs (int): Number of backtest observations (e.g. 250 days).
    n_exceedances (int): Number of observed VaR exceedances.
    confidence (float): VaR confidence level in (0, 1); the tested tail
    probability is alpha = 1 - confidence.
    transitions: optional dict {"n00", "n01", "n10", "n11"} of Markov
    transition counts; when given, the Christoffersen independence test and
    the conditional coverage statistic are included.

    Returns:
    dict: {"n_obs", "n_exceedances", "alpha", "kupiec_stat", "kupiec_p",
    "christoffersen_stat", "christoffersen_p", "conditional_coverage_stat",
    "conditional_coverage_p"} (Christoffersen entries only with transitions).
    """
    n_obs = int(n_obs)
    n_exceedances = int(n_exceedances)
    if n_obs < 1 or not 0 <= n_exceedances <= n_obs:
        raise ValueError("require n_obs >= 1 and 0 <= n_exceedances <= n_obs")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in the open interval (0, 1)")

    alpha = 1.0 - float(confidence)
    kupiec_stat, kupiec_p = kupiec_unconditional_coverage(n_obs, n_exceedances, alpha)
    result = {
        "n_obs": n_obs,
        "n_exceedances": n_exceedances,
        "alpha": float(alpha),
        "kupiec_stat": float(kupiec_stat),
        "kupiec_p": float(kupiec_p),
    }
    if transitions is not None:
        ind_stat, ind_p = christoffersen_independence(
            int(transitions["n00"]),
            int(transitions["n01"]),
            int(transitions["n10"]),
            int(transitions["n11"]),
        )
        cc_stat = kupiec_stat + ind_stat
        result["christoffersen_stat"] = float(ind_stat)
        result["christoffersen_p"] = float(ind_p)
        result["conditional_coverage_stat"] = float(cc_stat)
        result["conditional_coverage_p"] = float(1 - stats.chi2.cdf(cc_stat, df=2))
    return result


if __name__ == "__main__":
    # Example usage from text: 2000 observations, 33 exceedances, alpha = 0.01
    # Transitions: n11=2, n00=1936, n01=31, n10=31
    lr_uc_stat, lr_uc_p = kupiec_unconditional_coverage(2000, 33, 0.01)
    lr_ind_stat, lr_ind_p = christoffersen_independence(1936, 31, 31, 2)
    lr_cc_stat = lr_uc_stat + lr_ind_stat
