"""Joint probability of a compound stress scenario.

Evaluates the joint probability of a main risk-driver shock and a
secondary shock, where the secondary distribution is conditional on the
main shock: P(main) * P(secondary | main).
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.7.2.
"""

import scipy.stats as stats


def evaluate_joint_stress_scenario(
    main_driver_dist: stats.rv_continuous,
    main_shock_threshold: float,
    conditional_secondary_dist: stats.rv_continuous,
    secondary_shock_threshold: float,
    main_direction: str = "greater",
    secondary_direction: str = "less",
) -> float:
    """
    Calculates the joint probability of a compound hypothetical stress scenario
    using sequentially encoded conditional distributions.

    Example: Probability that Credit Spread increases > 100bps AND Interest Rate falls < -50bps.
    """
    # 1. Calculate the marginal probability of the main risk driver shock
    if main_direction == "greater":
        p_main = 1 - main_driver_dist.cdf(main_shock_threshold)
    else:
        p_main = main_driver_dist.cdf(main_shock_threshold)

    # 2. Calculate the conditional probability of the secondary shock
    if secondary_direction == "less":
        p_secondary_given_main = conditional_secondary_dist.cdf(secondary_shock_threshold)
    else:
        p_secondary_given_main = 1 - conditional_secondary_dist.cdf(secondary_shock_threshold)

    # 3. Calculate Joint Probability
    joint_probability = p_secondary_given_main * p_main

    return joint_probability


# Example Scenario (IV.7.2 Concept)
# Main Driver (Credit Spreads): Assumed Normal(mu=40, sigma=15)


def compute(
    main_driver_dist,
    main_shock_threshold: float,
    conditional_secondary_dist,
    secondary_shock_threshold: float,
    main_direction: str = "greater",
    secondary_direction: str = "less",
) -> dict:
    """Standard facade: joint stress-scenario probability as a JSON dict.

    Parameters:
    main_driver_dist: scipy.stats frozen distribution of the main driver.
    main_shock_threshold (float): Shock threshold for the main driver.
    conditional_secondary_dist: Frozen distribution of the secondary
    driver, conditional on the main shock.
    secondary_shock_threshold (float): Shock threshold for the secondary.
    main_direction, secondary_direction (str): "greater" or "less".

    Returns:
    dict: {"method", "joint_probability", "main_direction",
    "secondary_direction"}.
    """
    joint = evaluate_joint_stress_scenario(
        main_driver_dist,
        float(main_shock_threshold),
        conditional_secondary_dist,
        float(secondary_shock_threshold),
        main_direction,
        secondary_direction,
    )
    return {
        "method": "joint_stress_probability",
        "joint_probability": float(joint),
        "main_direction": str(main_direction),
        "secondary_direction": str(secondary_direction),
    }


if __name__ == "__main__":
    spread_dist = stats.norm(loc=40, scale=15)

    # Secondary Driver (Interest Rates) CONDITIONAL on Spread >= 80bps: Assumed Normal(mu=-60, sigma=25)
    rates_given_spread_shock = stats.norm(loc=-60, scale=25)

    # Find probability that Spread >= 80 bps AND Rates <= -80 bps
    joint_prob = evaluate_joint_stress_scenario(
        main_driver_dist=spread_dist,
        main_shock_threshold=80,
        conditional_secondary_dist=rates_given_spread_shock,
        secondary_shock_threshold=-80,
        main_direction="greater",
        secondary_direction="less",
    )
