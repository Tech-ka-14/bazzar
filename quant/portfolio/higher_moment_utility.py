"""Higher-moment certainty equivalent approximation.

Four-moment Taylor approximation of the certainty equivalent for an
exponential-utility investor with absolute risk aversion gamma:
CE ~ mu - (gamma/2) sigma^2 + (gamma^2/6) skew sigma^3 -
(gamma^3/24) kurt_excess sigma^4 (Example I.6.4, Alexander 2008).
"""


def higher_moment_certainty_equivalent(mu, sigma, skewness, excess_kurtosis, gamma):
    """
    Approximates the Certain Equivalent (CE) incorporating up to the 4th moment
    for an investor with an exponential utility function.
    """
    term_mean = mu
    term_variance = -(1 / 2) * gamma * (sigma**2)
    term_skewness = (skewness / 6) * (gamma**2) * (sigma**3)
    term_kurtosis = -(excess_kurtosis / 24) * (gamma**3) * (sigma**4)

    ce = term_mean + term_variance + term_skewness + term_kurtosis
    return ce


def compute(mu: float, sigma: float, skewness: float, excess_kurtosis: float, gamma: float) -> dict:
    """Standard facade: higher-moment certainty equivalent as a JSON dict.

    Parameters:
    mu (float): Expected return of the portfolio (fraction).
    sigma (float): Volatility of the portfolio (fraction), positive.
    skewness (float): Skewness of the return distribution.
    excess_kurtosis (float): Excess kurtosis of the return distribution.
    gamma (float): Investor's absolute risk aversion, non-negative.

    Returns:
    dict: {"mu", "sigma", "skewness", "excess_kurtosis", "gamma",
    "certainty_equivalent"} with the CE in the same units as mu.
    """
    sigma = float(sigma)
    gamma = float(gamma)
    if sigma <= 0.0:
        raise ValueError("sigma must be positive")
    if gamma < 0.0:
        raise ValueError("gamma must be non-negative")

    ce = higher_moment_certainty_equivalent(
        float(mu), sigma, float(skewness), float(excess_kurtosis), gamma
    )
    return {
        "mu": float(mu),
        "sigma": sigma,
        "skewness": float(skewness),
        "excess_kurtosis": float(excess_kurtosis),
        "gamma": gamma,
        "certainty_equivalent": float(ce),
    }


if __name__ == "__main__":
    # --- Example I.6.4 Implementation ---
    # Portfolio A parameters
    mu_A, sig_A, skew_A, kurt_A = 0.10, 0.12, -0.50, 2.50
    # Portfolio B parameters
    mu_B, sig_B, skew_B, kurt_B = 0.15, 0.20, -0.75, 1.50

    amount_invested = 1_000_000

    # Scenario (i): Risk tolerance = $200,000
    gamma_i = amount_invested / 200_000
    ce_A_i = higher_moment_certainty_equivalent(mu_A, sig_A, skew_A, kurt_A, gamma_i)
    ce_B_i = higher_moment_certainty_equivalent(mu_B, sig_B, skew_B, kurt_B, gamma_i)

    # Scenario (ii): Risk tolerance = $400,000
    gamma_ii = amount_invested / 400_000
    ce_A_ii = higher_moment_certainty_equivalent(mu_A, sig_A, skew_A, kurt_A, gamma_ii)
    ce_B_ii = higher_moment_certainty_equivalent(mu_B, sig_B, skew_B, kurt_B, gamma_ii)

    print("--- Higher Moment Certainty Equivalents ---")
    print("Scenario (i): Absolute Risk Tolerance = $200,000 (Gamma = 5)")
    print(f"  CE Portfolio A: ${ce_A_i * amount_invested:,.0f}")
    print(f"  CE Portfolio B: ${ce_B_i * amount_invested:,.0f}")
    print("  -> Prefer Portfolio A")

    print("\nScenario (ii): Absolute Risk Tolerance = $400,000 (Gamma = 2.5)")
    print(f"  CE Portfolio A: ${ce_A_ii * amount_invested:,.0f}")
    print(f"  CE Portfolio B: ${ce_B_ii * amount_invested:,.0f}")
    print("  -> Prefer Portfolio B")
