import numpy as np

def calculate_frechet_bounds(u1, u2):
    """
    Calculates the Independence copula, Fréchet Upper Bound, and 
    Fréchet Lower Bound for a given pair of uniform marginal probabilities.
    """
    # Ensure inputs are scalar floats or numpy arrays
    u1 = np.asarray(u1)
    u2 = np.asarray(u2)
    
    # 1. Independence Copula
    independence = u1 * u2
    
    # 2. Fréchet Upper Bound (Perfect Positive Dependence)
    upper_bound = np.minimum(u1, u2)
    
    # 3. Fréchet Lower Bound (Perfect Negative Dependence)
    lower_bound = np.maximum(u1 + u2 - 1, 0)
    
    return {
        "Independence (C)": independence,
        "Fréchet Upper Bound (W)": upper_bound,
        "Fréchet Lower Bound (M)": lower_bound
    }

# Example Evaluation at the median:
# What are the bounds when both variables are exactly at their 50th percentile?
bounds_at_median = calculate_frechet_bounds(0.50, 0.50)
print(bounds_at_median) 
# Output: C = 0.25 (Independent), W = 0.50 (Perfect Positive), M = 0.0 (Perfect Negative)