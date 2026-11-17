"""Expected utility and certainty equivalent.

Expected utility E[U(W)] = sum_i p_i U(w_i) over discrete wealth outcomes;
the certainty equivalent is U^{-1}(E[U(W)]), the guaranteed wealth giving
the same utility as the risky prospect (Examples I.6.1-I.6.2, Alexander 2008).
"""

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


_UTILITY_FUNCTIONS = {
    # name -> (utility, inverse utility)
    "sqrt": (lambda w: np.sqrt(w), lambda u: u**2),
    "log": (lambda w: np.log(w), lambda u: np.exp(u)),
    "power2": (lambda w: w**2, lambda u: np.sqrt(u)),
    "linear": (lambda w: w, lambda u: u),
}


def compute(probabilities, outcomes, utility: str = "sqrt") -> dict:
    """Standard facade: expected utility and CE as a JSON-serializable dict.

    Parameters:
    probabilities: 1-D array-like of outcome probabilities (must sum to 1).
    outcomes: 1-D array-like of wealth outcomes, same length.
    utility (str): One of "sqrt", "log", "power2", "linear".

    Returns:
    dict: {"utility", "n_outcomes", "expected_utility",
    "certainty_equivalent"} with plain floats.
    """
    probabilities = np.asarray(probabilities, dtype=float).ravel()
    outcomes = np.asarray(outcomes, dtype=float).ravel()
    if probabilities.size != outcomes.size or probabilities.size == 0:
        raise ValueError("probabilities and outcomes must have equal non-zero length")
    if not np.isclose(probabilities.sum(), 1.0):
        raise ValueError("probabilities must sum to 1")
    if utility not in _UTILITY_FUNCTIONS:
        raise ValueError(f"utility must be one of {sorted(_UTILITY_FUNCTIONS)}")
    if utility in ("sqrt", "log") and (outcomes <= 0).any():
        raise ValueError(f"outcomes must be strictly positive for the {utility} utility")

    u_func, inv_u_func = _UTILITY_FUNCTIONS[utility]
    eu = expected_utility(probabilities, outcomes, u_func)
    ce = certainty_equivalent(eu, inv_u_func)
    return {
        "utility": utility,
        "n_outcomes": int(outcomes.size),
        "expected_utility": float(eu),
        "certainty_equivalent": float(ce),
    }


if __name__ == "__main__":
    # --- Example I.6.1 & I.6.2 Implementation ---
    # Utility function U(W) = W^2, so Inverse is sqrt(U)
    def u_func(w):
        return w**2

    def inv_u_func(u):
        return np.sqrt(u)

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
