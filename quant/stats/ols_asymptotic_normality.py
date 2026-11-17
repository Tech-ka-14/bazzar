"""Asymptotic normality of the OLS estimator.

Monte Carlo demonstration that the OLS slope estimator becomes normally
distributed even with highly non-normal (exponential) errors, via the
Central Limit Theorem. Reference: Alexander (2008), Vol. I, Section I.4.
"""

import numpy as np
import scipy.stats as stats
import statsmodels.api as sm


def test_ols_asymptotic_normality(true_alpha, true_beta, sample_size, num_simulations):
    """
    Demonstrates that the OLS estimator becomes normally distributed
    even when the underlying error term is highly non-normal (Exponential),
    proving the Central Limit Theorem application for regressions.
    """
    estimated_betas = []

    # Generate deterministic X values
    x = np.linspace(1, 10, sample_size)
    x_with_constant = sm.add_constant(x)

    for _ in range(num_simulations):
        # Generate NON-NORMAL errors (Exponential distribution, heavily skewed)
        # Shift it so the mean error is 0 to satisfy OLS assumptions
        errors = np.random.exponential(scale=2.0, size=sample_size) - 2.0

        # Calculate Y
        y_sample = true_alpha + (true_beta * x) + errors

        # Fit OLS
        model = sm.OLS(y_sample, x_with_constant)
        results = model.fit()

        # Collect the estimated beta
        estimated_betas.append(results.params[1])

    # Analyze the resulting distribution of the estimators
    estimated_betas = np.array(estimated_betas)

    mean_beta = np.mean(estimated_betas)

    print("--- Asymptotic Normality (CLT) Test ---")
    print(f"Sample Size per Regression: {sample_size}")
    print(f"True Beta: {true_beta}, Average Estimated Beta: {mean_beta:.4f}")

    # Perform a Shapiro-Wilk test for Normality on the distribution of Betas
    # H0: The data is normally distributed.
    stat, p_value = stats.shapiro(estimated_betas)

    print("\nShapiro-Wilk Test for Normality:")
    print(f"Test Statistic: {stat:.4f}, p-value: {p_value:.4f}")

    if p_value > 0.05:
        print(
            "Conclusion: We CANNOT reject the null hypothesis. The OLS estimators are Normally Distributed!"
        )
    else:
        print("Conclusion: The distribution is not yet normal (Sample size might be too small).")


def compute(data, true_beta=2.5, sample_size=500, num_simulations=1000, seed=None) -> dict:
    """Standard facade: CLT simulation for the OLS slope estimator.

    Parameters:
    data (float): true intercept alpha of the data-generating process.
    true_beta (float): true slope of the data-generating process.
    sample_size (int): observations per regression.
    num_simulations (int): number of simulated regressions.
    seed (int, optional): RNG seed for reproducibility.

    Returns:
    dict: {"true_beta", "mean_beta", "shapiro_statistic",
    "shapiro_p_value", "normal_at_5pct"}; errors are drawn from a
    (re-centred) exponential distribution.
    """
    if int(sample_size) < 3:
        raise ValueError("sample_size must be at least 3")
    if int(num_simulations) < 20:
        raise ValueError("num_simulations must be at least 20 for the Shapiro-Wilk test")

    rng = np.random.default_rng(seed)
    x = np.linspace(1, 10, int(sample_size))
    x_with_constant = sm.add_constant(x)

    estimated_betas = []
    for _ in range(int(num_simulations)):
        errors = rng.exponential(scale=2.0, size=int(sample_size)) - 2.0
        y_sample = float(data) + float(true_beta) * x + errors
        estimated_betas.append(sm.OLS(y_sample, x_with_constant).fit().params[1])

    estimated_betas = np.asarray(estimated_betas)
    stat, p_value = stats.shapiro(estimated_betas)
    return {
        "true_beta": float(true_beta),
        "mean_beta": float(np.mean(estimated_betas)),
        "shapiro_statistic": float(stat),
        "shapiro_p_value": float(p_value),
        "normal_at_5pct": bool(p_value > 0.05),
    }


if __name__ == "__main__":
    # 1. Run with a SMALL sample size (CLT might not hold yet)
    print("TEST 1: Small Sample Size (N=10)")
    test_ols_asymptotic_normality(
        true_alpha=1.0, true_beta=2.5, sample_size=10, num_simulations=1000
    )

    print("\n" + "=" * 50 + "\n")

    # 2. Run with a LARGE sample size (CLT takes over)
    print("TEST 2: Large Sample Size (N=500)")
    test_ols_asymptotic_normality(
        true_alpha=1.0, true_beta=2.5, sample_size=500, num_simulations=1000
    )
