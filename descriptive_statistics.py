import numpy as np
import scipy.stats as stats

def calculate_sample_moments(data_array):
    """
    Calculates the first four moments of a data sample: 
    Mean, Variance, Skewness, and Kurtosis.
    """
    data = np.array(data_array)
    n = len(data)
    
    # 1. First Moment: Sample Mean
    mean = np.mean(data)
    
    # 2. Second Central Moment: Sample Variance
    # ddof=0 gives the biased estimator (divided by n)
    # ddof=1 gives the unbiased estimator (divided by n-1)
    biased_variance = np.var(data, ddof=0)
    unbiased_variance = np.var(data, ddof=1)
    
    # Standard deviation is the square root of variance
    volatility = np.sqrt(unbiased_variance)
    
    # 3. Third Central Moment: Skewness
    # Measures the asymmetry of the distribution
    skewness = stats.skew(data, bias=False) # bias=False applies the n-1 correction
    
    # 4. Fourth Central Moment: Kurtosis
    # Measures the "fatness" of the tails. 
    # Fisher's definition subtracts 3 so that normal distribution kurtosis = 0 (Excess Kurtosis)
    excess_kurtosis = stats.kurtosis(data, fisher=True, bias=False)
    
    print(f"--- Sample Statistics (n={n}) ---")
    print(f"Sample Mean: {mean:.4f}")
    print(f"Biased Variance (n): {biased_variance:.4f}")
    print(f"Unbiased Variance (n-1): {unbiased_variance:.4f}")
    print(f"Standard Deviation (Volatility): {volatility:.4f}")
    print(f"Skewness: {skewness:.4f}")
    print(f"Excess Kurtosis: {excess_kurtosis:.4f}")
    
    return mean, unbiased_variance, skewness, excess_kurtosis

# --- Testing with a hypothetical returns sample ---
if __name__ == "__main__":
    # Hypothetical daily percentage returns for an asset
    returns_data = [1.2, -0.5, 2.1, -1.8, 0.4, 0.9, -0.2, -3.1, 4.5, 0.1]
    
    calculate_sample_moments(returns_data)