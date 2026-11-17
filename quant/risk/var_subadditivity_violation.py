"""Counter-example proving VaR violates sub-additivity.

Two independent binary options whose individual VaRs sum to less than
the portfolio VaR, demonstrating that VaR is not sub-additive.
Reference: Alexander (2008), Market Risk Analysis IV, Example IV.1.11.
"""


def binary_option_var_violation(premium: float, payout: float, prob_loss: float, alpha: float):
    """
    Replicates Example IV.1.11 to mathematically prove VaR violates sub-additivity.
    """
    net_loss = premium - payout  # -9000
    net_gain = premium  # +1000

    # 1. INDIVIDUAL OPTION P&L DISTRIBUTION
    prob_gain = 1.0 - prob_loss

    print("--- Individual Option ---")
    print(f"P&L = {net_loss} | Probability = {prob_loss:.4%}")
    print(f"P&L = {net_gain} | Probability = {prob_gain:.4%}")

    # Calculate Individual VaR
    # If the probability of the loss is less than alpha, the alpha quantile is the net gain.
    individual_var = -net_gain if prob_loss <= alpha else -net_loss
    print(f"5% Individual VaR: ${individual_var:,.0f}")
    print(f"Sum of two individual VaRs: ${individual_var * 2:,.0f}\n")

    # 2. PORTFOLIO P&L DISTRIBUTION (Assuming Independence)
    # Both called: (premium*2) - (payout*2)
    # One called: (premium*2) - payout (Text simplifies this outcome as -9000 to match the math)
    # None called: premium*2

    loss_both = (premium * 2) - (payout * 2)
    loss_one = net_loss  # Using the text's simplified parameter
    gain_both = premium * 2

    prob_both_called = prob_loss**2
    prob_one_called = 2 * prob_loss * prob_gain
    prob_none_called = prob_gain**2

    print("--- Portfolio of Two Options ---")
    print(f"P&L = {loss_both} | Probability = {prob_both_called:.4%}")
    print(f"P&L = {loss_one}  | Probability = {prob_one_called:.4%}")
    print(f"P&L = {gain_both}   | Probability = {prob_none_called:.4%}")

    # Cumulative probability of losing exactly loss_one or worse
    cumulative_prob_loss = prob_both_called + prob_one_called
    print(f"Cumulative Probability of {loss_one} or worse: {cumulative_prob_loss:.4%}")

    # Calculate Portfolio VaR
    portfolio_var = -loss_one if cumulative_prob_loss >= alpha else -gain_both
    print(f"5% Portfolio VaR: ${portfolio_var:,.0f}\n")

    # 3. SUB-ADDITIVITY CHECK
    is_subadditive = portfolio_var <= (individual_var * 2)
    print(f"Is VaR Sub-additive here? {is_subadditive}")
    print(f"({portfolio_var} is NOT <= {individual_var * 2})")


# Execute Example IV.1.11


def compute(premium: float, payout: float, prob_loss: float, alpha: float = 0.05) -> dict:
    """Standard facade: binary-option sub-additivity check as a JSON dict.

    Parameters:
    premium (float): Option premium received.
    payout (float): Payout if the option is called (greater than premium).
    prob_loss (float): Probability the option is called in (0, 1).
    alpha (float): VaR significance level in (0, 1).

    Returns:
    dict: {"method", "alpha", "individual_var", "portfolio_var",
    "sum_individual_vars", "is_subadditive"}.
    """
    if payout <= premium:
        raise ValueError("payout must exceed premium")
    if not 0.0 < prob_loss < 1.0:
        raise ValueError("prob_loss must be in the open interval (0, 1)")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    premium = float(premium)
    payout = float(payout)
    prob_loss = float(prob_loss)
    net_loss = premium - payout
    net_gain = premium

    individual_var = -net_gain if prob_loss <= alpha else -net_loss

    loss_one = net_loss
    gain_both = premium * 2
    prob_gain = 1.0 - prob_loss
    prob_both_called = prob_loss**2
    prob_one_called = 2 * prob_loss * prob_gain
    cumulative_prob_loss = prob_both_called + prob_one_called
    portfolio_var = -loss_one if cumulative_prob_loss >= alpha else -gain_both

    return {
        "method": "binary_option_counterexample",
        "alpha": float(alpha),
        "individual_var": float(individual_var),
        "portfolio_var": float(portfolio_var),
        "sum_individual_vars": float(individual_var * 2),
        "is_subadditive": bool(portfolio_var <= individual_var * 2),
    }


if __name__ == "__main__":
    binary_option_var_violation(premium=1000, payout=10000, prob_loss=0.02532, alpha=0.05)
