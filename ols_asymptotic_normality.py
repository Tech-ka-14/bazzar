import numpy as np
import statsmodels.api as sm
import scipy.stats as stats

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
    
    print(f"--- Asymptotic Normality (CLT) Test ---")
    print(f"Sample Size per Regression: {sample_size}")
    print(f"True Beta: {true_beta}, Average Estimated Beta: {mean_beta:.4f}")
    
    # Perform a Shapiro-Wilk test for Normality on the distribution of Betas
    # H0: The data is normally distributed.
    stat, p_value = stats.shapiro(estimated_betas)
    
    print(f"\nShapiro-Wilk Test for Normality:")
    print(f"Test Statistic: {stat:.4f}, p-value: {p_value:.4f}")
    
    if p_value > 0.05:
        print("Conclusion: We CANNOT reject the null hypothesis. The OLS estimators are Normally Distributed!")
    else:
        print("Conclusion: The distribution is not yet normal (Sample size might be too small).")

# 1. Run with a SMALL sample size (CLT might not hold yet)
print("TEST 1: Small Sample Size (N=10)")
test_ols_asymptotic_normality(true_alpha=1.0, true_beta=2.5, sample_size=10, num_simulations=1000)

print("\n" + "="*50 + "\n")

# 2. Run with a LARGE sample size (CLT takes over)
print("TEST 2: Large Sample Size (N=500)")
test_ols_asymptotic_normality(true_alpha=1.0, true_beta=2.5, sample_size=500, num_simulations=1000)