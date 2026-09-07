import numpy as np
import statsmodels.api as sm


def run_ols_sampling_distribution_demo(
    true_alpha, true_beta, x_range, error_std, n_samples, n_simulations
):
    """
    Demonstrates that OLS estimators are random variables with their own
    sampling distributions, centered on the true population parameters.
    """
    estimated_alphas = []
    estimated_betas = []

    for _ in range(n_simulations):
        # 1. Simulate a sample from the true population model
        X_vals = np.random.uniform(x_range[0], x_range[1], n_samples)
        # The true error process (unexplained noise)
        errors = np.random.normal(0, error_std, n_samples)

        # True structural relationship
        Y_vals = true_alpha + true_beta * X_vals + errors

        # 2. Estimate the model using OLS on this specific sample
        X_design = sm.add_constant(X_vals)
        model = sm.OLS(Y_vals, X_design)
        results = model.fit()

        # Store the estimated parameters
        estimated_alphas.append(results.params[0])
        estimated_betas.append(results.params[1])

    # 3. Analyze the sampling distribution of the estimators
    mean_alpha = np.mean(estimated_alphas)
    std_alpha = np.std(estimated_alphas)

    mean_beta = np.mean(estimated_betas)
    std_beta = np.std(estimated_betas)

    print("--- OLS Sampling Distribution Simulation ---")
    print(f"True Population Alpha: {true_alpha:.2f}")
    print(f"Mean of Estimated Alphas: {mean_alpha:.4f} (Should be very close to true)")
    print(f"Std Dev of Alphas (Standard Error): {std_alpha:.4f}\n")

    print(f"True Population Beta: {true_beta:.2f}")
    print(f"Mean of Estimated Betas: {mean_beta:.4f} (Should be very close to true)")
    print(f"Std Dev of Betas (Standard Error): {std_beta:.4f}")


# Run the demonstration
run_ols_sampling_distribution_demo(
    true_alpha=5.0, true_beta=2.5, x_range=(0, 20), error_std=3.0, n_samples=50, n_simulations=1000
)
