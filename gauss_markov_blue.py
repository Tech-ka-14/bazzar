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

def prove_gauss_markov_theorem(true_alpha, true_beta, error_volatility, sample_size, num_simulations):
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
    
    print(f"--- GAUSS-MARKOV THEOREM SIMULATION ---")
    print(f"True Beta: {true_beta}\n")
    
    print("1. Ordinary Least Squares (OLS) Estimator:")
    print(f"   Expected Value: {ols_mean:.4f} (Unbiased)")
    print(f"   Variance:       {ols_variance:.6f} ('Best' / Most Efficient)\n")
    
    print("2. Alternative Linear Estimator (First/Last Point):")
    print(f"   Expected Value: {alt_mean:.4f} (Unbiased)")
    print(f"   Variance:       {alt_variance:.6f} (Inefficient)\n")
    
    if ols_variance < alt_variance:
        print("Conclusion: The Gauss-Markov theorem holds. OLS is more efficient (BLUE).")

# Run the proof
prove_gauss_markov_theorem(true_alpha=5.0, true_beta=2.0, error_volatility=3.0, sample_size=50, num_simulations=5000)