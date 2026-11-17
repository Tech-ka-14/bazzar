"""Monte Carlo proof of the Gauss-Markov theorem.

Simulates repeated regressions to show OLS has smaller variance than an
alternative linear unbiased estimator (OLS is BLUE). Reference: Alexander
(2008), Vol. I, Section I.4.
"""

import numpy as np
import statsmodels.api as sm


def alternative_linear_unbiased_estimator(x, y):
    """
    An alternative estimator that only uses the first and last data points
    to calculate the slope: (Y_n - Y_1) / (X_n - X_1).
    Because E(error) = 0, this is still unbiased. Because it's a linear
    combination of Y, it is linear. However, it is highly inefficient!
    """
    # Assuming x is sorted ascending for simplicity
    slope_estimate = (y[-1] - y[0]) / (x[-1] - x[0])
    return slope_estimate


def prove_gauss_markov_theorem(
    true_alpha, true_beta, error_volatility, sample_size, num_simulations
):
    """
    Simulates thousands of regressions to prove that OLS has a smaller
    variance than an alternative linear unbiased estimator (BLUE property).
    """
    ols_estimates = []
    alt_estimates = []

    # Generate X once (deterministic explanatory variables as per the theorem)
    x = np.linspace(1, 10, sample_size)
    x_with_constant = sm.add_constant(x)

    for _ in range(num_simulations):
        # Generate i.i.d. errors
        errors = np.random.normal(0, error_volatility, sample_size)
        y_sample = true_alpha + (true_beta * x) + errors

        # 1. Estimate using OLS
        model = sm.OLS(y_sample, x_with_constant)
        results = model.fit()
        ols_estimates.append(results.params[1])

        # 2. Estimate using the Alternative LUE
        alt_beta = alternative_linear_unbiased_estimator(x, y_sample)
        alt_estimates.append(alt_beta)

    # Calculate distributions
    ols_mean, ols_variance = np.mean(ols_estimates), np.var(ols_estimates)
    alt_mean, alt_variance = np.mean(alt_estimates), np.var(alt_estimates)

    print("--- GAUSS-MARKOV THEOREM SIMULATION ---")
    print(f"True Beta: {true_beta}\n")

    print("1. Ordinary Least Squares (OLS) Estimator:")
    print(f"   Expected Value: {ols_mean:.4f} (Unbiased)")
    print(f"   Variance:       {ols_variance:.6f} ('Best' / Most Efficient)\n")

    print("2. Alternative Linear Estimator (First/Last Point):")
    print(f"   Expected Value: {alt_mean:.4f} (Unbiased)")
    print(f"   Variance:       {alt_variance:.6f} (Inefficient)\n")

    if ols_variance < alt_variance:
        print("Conclusion: The Gauss-Markov theorem holds. OLS is more efficient (BLUE).")


def compute(
    data,
    true_beta=2.0,
    error_volatility=3.0,
    sample_size=50,
    num_simulations=1000,
    seed=None,
) -> dict:
    """Standard facade: Gauss-Markov simulation as a JSON dict.

    Parameters:
    data (float): true intercept alpha of the data-generating process.
    true_beta (float): true slope of the data-generating process.
    error_volatility (float): standard deviation of the i.i.d. normal errors.
    sample_size (int): observations per regression.
    num_simulations (int): number of simulated regressions.
    seed (int, optional): RNG seed for reproducibility.

    Returns:
    dict: {"ols_mean", "ols_variance", "alternative_mean",
    "alternative_variance", "ols_is_more_efficient"} where the alternative
    estimator uses only the first and last sample points.
    """
    if int(sample_size) < 3:
        raise ValueError("sample_size must be at least 3")
    if int(num_simulations) < 2:
        raise ValueError("num_simulations must be at least 2")
    if float(error_volatility) <= 0.0:
        raise ValueError("error_volatility must be positive")

    rng = np.random.default_rng(seed)
    x = np.linspace(1, 10, int(sample_size))
    x_with_constant = sm.add_constant(x)

    ols_estimates = []
    alt_estimates = []
    for _ in range(int(num_simulations)):
        errors = rng.normal(0.0, float(error_volatility), int(sample_size))
        y_sample = float(data) + float(true_beta) * x + errors
        ols_estimates.append(sm.OLS(y_sample, x_with_constant).fit().params[1])
        alt_estimates.append(alternative_linear_unbiased_estimator(x, y_sample))

    ols_variance = float(np.var(ols_estimates))
    alt_variance = float(np.var(alt_estimates))
    return {
        "ols_mean": float(np.mean(ols_estimates)),
        "ols_variance": ols_variance,
        "alternative_mean": float(np.mean(alt_estimates)),
        "alternative_variance": alt_variance,
        "ols_is_more_efficient": bool(ols_variance < alt_variance),
    }


if __name__ == "__main__":
    # Run the proof
    prove_gauss_markov_theorem(
        true_alpha=5.0, true_beta=2.0, error_volatility=3.0, sample_size=50, num_simulations=5000
    )
