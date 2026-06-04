import numpy as np
import pandas as pd

def binary_option_var_violation(premium: float, payout: float, prob_loss: float, alpha: float):
    """
    Replicates Example IV.1.11 to mathematically prove VaR violates sub-additivity.
    """
    net_loss = premium - payout # -9000
    net_gain = premium          # +1000
    
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
    loss_one = net_loss # Using the text's simplified parameter
    gain_both = premium * 2
    
    prob_both_called = prob_loss ** 2
    prob_one_called = 2 * prob_loss * prob_gain
    prob_none_called = prob_gain ** 2
    
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
binary_option_var_violation(premium=1000, payout=10000, prob_loss=0.02532, alpha=0.05)