import numpy as np

def normal_mle_parameters(data):
    """
    Calculates the Maximum Likelihood Estimators for a normal distribution.
    Note: The MLE for variance divides by n, not n-1.
    """
    n = len(data)
    mle_mean = np.sum(data) / n
    # Alternatively: mle_mean = np.mean(data)
    
    mle_variance = np.sum((data - mle_mean)**2) / n
    # Alternatively: mle_variance = np.var(data, ddof=0)
    
    return mle_mean, mle_variance

def normal_mle_standard_errors(mle_variance, n):
    """
    Calculates the standard errors of the MLE estimates for a normal distribution
    using the diagonal elements of the inverse Information Matrix.
    """
    mle_std = np.sqrt(mle_variance)
    
    # Standard error of the mean: sigma / sqrt(n)
    se_mean = mle_std / np.sqrt(n)
    
    # Standard error of the variance: sigma^2 / sqrt(2n)
    se_variance = mle_variance / np.sqrt(2 * n)
    
    return se_mean, se_variance

# Example Usage
sample_data = np.array([0.01, -0.02, 0.015, 0.005, -0.01])
n_obs = len(sample_data)

mean_est, var_est = normal_mle_parameters(sample_data)
se_mu, se_var = normal_mle_standard_errors(var_est, n_obs)

print(f"MLE Mean: {mean_est:.4f} (SE: {se_mu:.4f})")
print(f"MLE Variance: {var_est:.6f} (SE: {se_var:.6f})")