import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm


def negative_log_likelihood(params, data):
    """
    Computes the negative log-likelihood for a normal distribution.
    We minimize the negative log-likelihood to find the MLEs.
    """
    mu, sigma = params
    n = len(data)

    # Log-likelihood formula: -n/2 * ln(2*pi) - n/2 * ln(sigma^2) - (1/(2*sigma^2)) * sum((x_i - mu)^2)
    # We use sigma (standard deviation) as the parameter, so sigma^2 = sigma**2
    log_likelihood = (
        -(n / 2) * np.log(2 * np.pi)
        - (n / 2) * np.log(sigma**2)
        - (1 / (2 * sigma**2)) * np.sum((data - mu) ** 2)
    )

    # Return negative because scipy.optimize minimizes functions
    return -log_likelihood


def fit_normal_mle(data):
    """
    Fits a normal distribution to the data using Maximum Likelihood Estimation
    and computes the Hessian matrix for standard errors.
    """
    data = np.array(data)

    # Initial guesses: sample mean and sample standard deviation
    initial_mu = np.mean(data)
    initial_sigma = np.std(data)
    initial_params = [initial_mu, initial_sigma]

    # Minimize the negative log-likelihood
    # method='BFGS' approximates the Hessian, which we need for standard errors
    result = minimize(
        negative_log_likelihood, initial_params, args=(data,), method="BFGS"
    )

    mle_mu, mle_sigma = result.x

    # The inverse of the Hessian matrix is the estimated covariance matrix of the parameters
    # The diagonal elements are the variances. Square roots are the standard errors.
    covariance_matrix = result.hess_inv
    se_mu = np.sqrt(covariance_matrix[0, 0])
    se_sigma = np.sqrt(covariance_matrix[1, 1])

    print("--- Maximum Likelihood Estimation Results ---")
    print(f"MLE Mean (mu): {mle_mu:.4f} (Standard Error: {se_mu:.4f})")
    print(f"MLE Volatility (sigma): {mle_sigma:.4f} (Standard Error: {se_sigma:.4f})")

    return mle_mu, mle_sigma, se_mu, se_sigma


# --- Testing with a simulated sample of returns ---
if __name__ == "__main__":
    # Generate 1000 returns from a true normal distribution (mu=0.05, sigma=0.20)
    np.random.seed(42)
    true_mu = 0.05
    true_sigma = 0.20
    sample_returns = np.random.normal(true_mu, true_sigma, 1000)

    fit_normal_mle(sample_returns)
