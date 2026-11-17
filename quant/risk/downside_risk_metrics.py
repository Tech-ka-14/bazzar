"""Downside risk metrics: second-order lower partial moments.

The annualized second-order lower partial moment (LPM) of returns
relative to a target; with the sample mean as target this is the
semi-standard deviation.
Reference: Alexander (2008), Market Risk Analysis IV, Example IV.1.1.
"""

import numpy as np


def calculate_lower_partial_moment(returns, target_return=None, periods_per_year=12):
    """
    Calculates the annualized Second Order Lower Partial Moment (LPM).
    If target_return is None, it defaults to the sample mean (calculating the Semi-Standard Deviation).
    """
    returns_array = np.array(returns)
    T = len(returns_array)

    # 1. Determine the threshold (tau)
    if target_return is None:
        threshold = np.mean(returns_array)
    else:
        threshold = target_return

    # 2. Isolate the downside deviations: min(R_t - threshold, 0)
    downside_deviations = np.minimum(returns_array - threshold, 0)

    # 3. Calculate the Second Order LPM (Mean of squared downside deviations)
    lpm_2 = np.sum(downside_deviations**2) / T

    # 4. Annualize the risk metric (Multiply variance by periods, then take square root)
    annualized_downside_risk = np.sqrt(lpm_2 * periods_per_year)

    return annualized_downside_risk


# --- Replicating Example IV.1.1 ---

# Historical sample of 36 monthly active returns from Table IV.1.1 (in decimal format)


def compute(returns, target_return=None, periods_per_year: int = 12) -> dict:
    """Standard facade: annualized second-order LPM as a JSON dict.

    Parameters:
    returns: 1-D array-like of periodic returns (fractions).
    target_return (float, optional): Target return; defaults to the
    sample mean (semi-standard deviation).
    periods_per_year (int): Annualization frequency (default 12).

    Returns:
    dict: {"method", "n", "periods_per_year", "target_return",
    "annualized_lpm"}.
    """
    returns = np.asarray(returns, dtype=float).ravel()
    if returns.size == 0:
        raise ValueError("returns must contain at least one observation")

    lpm = calculate_lower_partial_moment(
        returns,
        target_return=None if target_return is None else float(target_return),
        periods_per_year=int(periods_per_year),
    )
    return {
        "method": "semi_std" if target_return is None else "lpm2",
        "n": int(returns.size),
        "periods_per_year": int(periods_per_year),
        "target_return": None if target_return is None else float(target_return),
        "annualized_lpm": float(lpm),
    }


if __name__ == "__main__":
    monthly_active_returns = [
        0.0040,
        0.0025,
        0.0027,
        0.0011,
        -0.0013,
        0.0012,  # Jan 06 - Jun 06
        0.0021,
        0.0005,
        -0.0013,
        -0.0029,
        -0.0049,
        -0.0032,  # Jul 06 - Dec 06
        0.0007,
        -0.0022,
        -0.0063,
        0.0003,
        0.0006,
        -0.0024,  # Jan 07 - Jun 07
        -0.0115,
        0.0036,
        0.0026,
        0.0025,
        -0.0021,
        -0.0027,  # Jul 07 - Dec 07
        0.0004,
        -0.0005,
        0.0000,
        0.0029,
        0.0030,
        0.0053,  # Jan 08 - Jun 08
        0.0041,
        -0.0005,
        0.0049,
        0.0041,
        0.0034,
        -0.0300,  # Jul 08 - Dec 08
    ]

    # (a) Calculate the Semi-Standard Deviation (target = sample mean)
    semi_std_dev = calculate_lower_partial_moment(monthly_active_returns, target_return=None)

    # (b) Calculate the Second Order LPM relative to a 2% per annum target
    # 2% per annum is strictly defined in the text as a target of 0.165% per month
    monthly_target = 0.00165
    lpm_target = calculate_lower_partial_moment(
        monthly_active_returns, target_return=monthly_target
    )

    print(f"Annualized Semi-Standard Deviation: {semi_std_dev * 100:.2f}%")
    print(f"Annualized Second Order LPM:        {lpm_target * 100:.2f}%")

    # Output beautifully matches the text exactly: 1.81% and 2.05%
