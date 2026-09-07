import numpy as np
import scipy.stats as stats
import statsmodels.api as sm


def demonstrate_clt_regression_coefficients(
    true_alpha, true_beta, sample_size, num_simulations=1000
):
    """
    Simulates multiple samples to show that OLS estimators asymptotically
    converge to a normal distribution centered on the true parameters.
    """
    estimated_alphas = []
    estimated_betas = []

    for _ in range(num_simulations):
        # 1. Generate a sample with a non-normal (e.g., uniform) error process
        # This proves CLT works even when errors aren't perfectly normal
        x = np.random.uniform(0, 10, sample_size)
        errors = np.random.uniform(-5, 5, sample_size)  # Non-normal errors!
        y = true_alpha + true_beta * x + errors

        # 2. Run OLS
        X = sm.add_constant(x)
        model = sm.OLS(y, X)
        results = model.fit()

        estimated_alphas.append(results.params[0])
        estimated_betas.append(results.params[1])

    # 3. Analyze the distribution of the estimators
    mean_beta = np.mean(estimated_betas)
    std_beta = np.std(estimated_betas)

    # Perform a normality test on the distribution of beta estimates
    ks_stat, p_value = stats.kstest(estimated_betas, "norm", args=(mean_beta, std_beta))

    print("--- CLT Demonstration for OLS Estimators ---")
    print(f"True Beta: {true_beta}")
    print(f"Mean of estimated Betas across {num_simulations} samples: {mean_beta:.4f}")
    print(f"Std Dev of estimated Betas (Standard Error): {std_beta:.4f}")
    print(f"Normality Test on Beta distribution (p-value): {p_value:.4f}")
    if p_value > 0.05:
        print("Conclusion: Fail to reject normality. The estimators are asymptotically normal.")
    else:
        print("Conclusion: The distribution is not yet normal (may need a larger sample size).")


# Run demonstration with T=100
demonstrate_clt_regression_coefficients(true_alpha=5.0, true_beta=2.0, sample_size=100)
