def higher_moment_certainty_equivalent(mu, sigma, skewness, excess_kurtosis, gamma):
    """
    Approximates the Certain Equivalent (CE) incorporating up to the 4th moment 
    for an investor with an exponential utility function.
    """
    term_mean = mu
    term_variance = - (1/2) * gamma * (sigma**2)
    term_skewness = (skewness / 6) * (gamma**2) * (sigma**3)
    term_kurtosis = - (excess_kurtosis / 24) * (gamma**3) * (sigma**4)
    
    ce = term_mean + term_variance + term_skewness + term_kurtosis
    return ce

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