import numpy as np

def generate_antithetic_uniforms(n_simulations: int) -> np.ndarray:
    """
    Generates a uniform sample where the second half is the antithetic pair of the first half.
    """
    half_n = n_simulations // 2
    u_first_half = np.random.uniform(0, 1, half_n)
    
    # The antithetic pairs
    u_second_half = 1.0 - u_first_half
    
    return np.concatenate((u_first_half, u_second_half))

def generate_stratified_uniforms(n_simulations: int, n_strata: int) -> np.ndarray:
    """
    Generates a stratified uniform sample to ensure even coverage across the unit interval.
    """
    samples_per_strata = n_simulations // n_strata
    stratified_samples = []
    
    for k in range(n_strata):
        # Generate random samples mapped strictly to the bounds of the k-th stratum
        u = np.random.uniform(0, 1, samples_per_strata)
        stratum_u = (u + k) / n_strata
        stratified_samples.append(stratum_u)
        
    return np.concatenate(stratified_samples)