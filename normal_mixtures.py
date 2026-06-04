import scipy.stats as stats

def normal_mixture_stats(weights, variances):
    """
    Calculates the overall variance and kurtosis of a zero-mean normal mixture.
    Based on Equations I.3.45 and I.3.46.
    """
    if sum(weights) != 1.0:
        raise ValueError("Probabilities must sum to 1.")
        
    # Variance of the mixture
    mixture_variance = sum(w * var for w, var in zip(weights, variances))
    
    # Kurtosis of the mixture
    numerator = sum(w * (var ** 2) for w, var in zip(weights, variances))
    denominator = mixture_variance ** 2
    mixture_kurtosis = 3 * (numerator / denominator)
    
    return mixture_variance, mixture_kurtosis

def normal_mixture_cdf(x, weights, means, std_devs):
    """
    Calculates the probability that the mixture variable X is less than x.
    Based on Equation I.3.51.
    """
    cumulative_prob = 0
    for w, mu, sigma in zip(weights, means, std_devs):
        # Calculate P(X < x) for each component and multiply by its weight
        prob = stats.norm.cdf(x, loc=mu, scale=sigma)
        cumulative_prob += w * prob
        
    return cumulative_prob

# --- Testing with Examples I.3.8 and I.3.9 ---
if __name__ == "__main__":
    print("--- Example I.3.8: Zero-Mean Mixture Stats ---")
    weights = [0.5, 0.5]
    std_devs = [0.03, 0.04]
    variances = [s**2 for s in std_devs]
    
    mix_var, mix_kurtosis = normal_mixture_stats(weights, variances)
    print(f"Mixture Standard Deviation: {mix_var**0.5:.4f}")
    print(f"Mixture Kurtosis: {mix_kurtosis:.3f}")
    
    print("\n--- Example I.3.9: Mixture Probabilities ---")
    w = [0.25, 0.75]
    mu = [1, -2]
    sigma = [4, 3]
    target_x = -1
    
    p_less_than_target = normal_mixture_cdf(target_x, w, mu, sigma)
    print(f"Probability P(X < -1): {p_less_than_target:.5f}")