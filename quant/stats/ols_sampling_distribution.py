"""Sampling distribution of the OLS estimator.

Monte Carlo demonstration that the OLS slope estimator is a random variable
with a normal sampling distribution centred on the true beta. Reference:
Alexander (2008), Vol. I, Section I.4.
"""

import numpy as np
import scipy.stats as stats
import statsmodels.api as sm


def simulate_ols_sampling_distribution(
    true_alpha, true_beta, error_volatility, sample_size, num_simulations
):
    """
    Demonstrates that the OLS estimator is a random variable with a normal
    sampling distribution by running repeated regressions on simulated data.
    """
    estimated_betas = []

    # Generate the independent variable X once (fixed across samples for simplicity)
    x = np.linspace(0, 10, sample_size)
    x_with_constant = sm.add_constant(x)

    for _ in range(num_simulations):
        # 1. Generate normal, i.i.d. errors for this specific sample
        errors = np.random.normal(0, error_volatility, sample_size)

        # 2. Calculate the theoretical Y and add the random errors
        y_sample = true_alpha + (true_beta * x) + errors

        # 3. Apply the OLS Estimator to get the Estimate for this sample
        model = sm.OLS(y_sample, x_with_constant)
        results = model.fit()

        # Store the estimated beta
        estimated_betas.append(results.params[1])

    estimated_betas = np.array(estimated_betas)

    # Calculate the properties of the estimator's sampling distribution
    mean_of_estimates = np.mean(estimated_betas)
    std_of_estimates = np.std(estimated_betas)

    print(f"True Theoretical Beta: {true_beta}")
    print(f"Mean of Estimated Betas: {mean_of_estimates:.4f}")
    print(f"Standard Error of the Estimator (Simulated): {std_of_estimates:.4f}")

    # Test if the sampling distribution is Normal (Shapiro-Wilk test)
    # A high p-value indicates we cannot reject the assumption of normality
    _, p_value_normality = stats.shapiro(estimated_betas)
    print(f"Normality Test p-value: {p_value_normality:.4f}")

    return estimated_betas


def compute(
    data,
    true_beta=1.5,
    error_volatility=3.0,
    sample_size=50,
    num_simulations=1000,
    seed=None,
) -> dict:
    """Standard facade: simulated OLS sampling-distribution summary.

    Parameters:
    data (float): true intercept alpha of the data-generating process.
    true_beta (float): true slope of the data-generating process.
    error_volatility (float): standard deviation of the i.i.d. normal errors.
    sample_size (int): observations per regression.
    num_simulations (int): number of simulated regressions.
    seed (int, optional): RNG seed for reproducibility.

    Returns:
    dict: {"true_beta", "mean_beta", "std_beta", "normality_p_value"}.
    """
    if int(sample_size) < 3:
        raise ValueError("sample_size must be at least 3")
    if int(num_simulations) < 20:
        raise ValueError("num_simulations must be at least 20 for the Shapiro-Wilk test")
    if float(error_volatility) <= 0.0:
        raise ValueError("error_volatility must be positive")

    rng = np.random.default_rng(seed)
    x = np.linspace(0, 10, int(sample_size))
    x_with_constant = sm.add_constant(x)

    estimated_betas = []
    for _ in range(int(num_simulations)):
        errors = rng.normal(0.0, float(error_volatility), int(sample_size))
        y_sample = float(data) + float(true_beta) * x + errors
        estimated_betas.append(sm.OLS(y_sample, x_with_constant).fit().params[1])

    estimated_betas = np.asarray(estimated_betas)
    _, p_value = stats.shapiro(estimated_betas)
    return {
        "true_beta": float(true_beta),
        "mean_beta": float(np.mean(estimated_betas)),
        "std_beta": float(np.std(estimated_betas)),
        "normality_p_value": float(p_value),
    }


if __name__ == "__main__":
    # --- Run the Simulation ---
    # Set our theoretical "true" model parameters
    TRUE_ALPHA = 2.0
    TRUE_BETA = 1.5
    ERROR_VOL = 3.0
    N_OBSERVATIONS = 50
    N_SIMULATIONS = 1000

    print("Simulating the OLS Estimator Sampling Distribution...\n")
    beta_distribution = simulate_ols_sampling_distribution(
        true_alpha=TRUE_ALPHA,
        true_beta=TRUE_BETA,
        error_volatility=ERROR_VOL,
        sample_size=N_OBSERVATIONS,
        num_simulations=N_SIMULATIONS,
    )
