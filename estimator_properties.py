import numpy as np

def evaluate_estimator(true_parameter, bias, variance, num_simulations=10000):
    """
    Simulates the sampling distribution of an estimator to calculate 
    its expected value and variance.
    """
    # The expected value of the estimator is the true parameter + any systematic bias
    expected_value = true_parameter + bias
    
    # Simulate thousands of estimates drawn from this estimator's distribution
    estimates = np.random.normal(loc=expected_value, scale=np.sqrt(variance), size=num_simulations)
    
    # Calculate the statistical properties of the simulated distribution
    calc_mean = np.mean(estimates)
    calc_variance = np.var(estimates)
    
    return calc_mean, calc_variance

# --- Demonstrating Unbiasedness and Efficiency ---
TRUE_BETA = 2.0

print("1. Unbiased & Efficient (The Ideal):")
m1, v1 = evaluate_estimator(TRUE_BETA, bias=0.0, variance=0.1)
print(f"Mean: {m1:.2f} (Matches True: {TRUE_BETA}), Variance: {v1:.2f} (Very tight)\n")

print("2. Unbiased & Inefficient (Not Robust):")
m2, v2 = evaluate_estimator(TRUE_BETA, bias=0.0, variance=5.0)
print(f"Mean: {m2:.2f} (Matches True: {TRUE_BETA}), Variance: {v2:.2f} (Highly volatile)\n")

print("3. Biased & Efficient (The 'Worst Case' per the text):")
m3, v3 = evaluate_estimator(TRUE_BETA, bias=1.5, variance=0.1)
print(f"Mean: {m3:.2f} (Systematically off), Variance: {v3:.2f} (Consistently wrong)\n")


# --- Demonstrating Consistency ---
def demonstrate_consistency(true_parameter, noise_variance, sample_sizes):
    """
    Shows how the variance of an estimator shrinks as sample size N increases,
    converging on the true parameter. (Variance of the mean = sigma^2 / N)
    """
    print("--- Consistency Demonstration ---")
    for n in sample_sizes:
        # As N increases, the variance of the estimator shrinks
        estimator_variance = noise_variance / n
        m, v = evaluate_estimator(true_parameter, bias=0.0, variance=estimator_variance)
        print(f"Sample Size (N) = {n:4d} | Estimator Variance: {v:.4f}")

demonstrate_consistency(true_parameter=2.0, noise_variance=10.0, sample_sizes=[10, 100, 1000, 10000])