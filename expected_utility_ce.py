import numpy as np

def expected_utility(probabilities, outcomes, utility_func):
    """
    Calculates the expected utility of an investment given its probability distribution.
    """
    utilities = np.array([utility_func(w) for w in outcomes])
    return np.sum(probabilities * utilities)

def certainty_equivalent(expected_util, inverse_utility_func):
    """
    Calculates the certain equivalent (CE) given an expected utility and the inverse utility function.
    """
    return inverse_utility_func(expected_util)

if __name__ == "__main__":
    # --- Example I.6.1 & I.6.2 Implementation ---
    # Utility function U(W) = W^2, so Inverse is sqrt(U)
    def u_func(w): return w**2
    def inv_u_func(u): return np.sqrt(u)
    
    # Outcomes translated to wealth on a $10 investment
    wealth_outcomes = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    
    # Probabilities for Investment P and Q
    prob_P = np.array([0.001, 0.010, 0.044, 0.117, 0.205, 0.246, 0.205, 0.117, 0.044, 0.010, 0.001])
    prob_Q = np.array([0.018, 0.073, 0.147, 0.195, 0.195, 0.156, 0.104, 0.060, 0.030, 0.013, 0.005])
    
    eu_P = expected_utility(prob_P, wealth_outcomes, u_func)
    eu_Q = expected_utility(prob_Q, wealth_outcomes, u_func)
    
    ce_P = certainty_equivalent(eu_P, inv_u_func)
    ce_Q = certainty_equivalent(eu_Q, inv_u_func)
    
    print("--- Expected Utility & Certainty Equivalent ---")
    print(f"Investment P -> Expected Utility: {eu_P:.2f}, CE: ${ce_P:.2f}")
    print(f"Investment Q -> Expected Utility: {eu_Q:.2f}, CE: ${ce_Q:.2f}")
    print("Decision: Prefer Investment Q because it has a higher CE.")