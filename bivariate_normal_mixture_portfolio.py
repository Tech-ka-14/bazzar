import numpy as np

def mixture_portfolio_components(w, pi_1, pi_2, mu_vectors, cov_matrices):
    """
    Calculates the mixing law (probabilities), expectations, and variances 
    for the four components of a linear portfolio consisting of two assets 
    that follow a bivariate normal mixture distribution.
    Based on Equations I.3.102, I.3.103, and I.3.104.
    
    :param w: Weight of asset 1 (weight of asset 2 is 1 - w)
    :param pi_1: Probability of regime 1 for asset 1
    :param pi_2: Probability of regime 1 for asset 2
    :param mu_vectors: List of 4 mean vectors [mu1, mu2, mu3, mu4]
    :param cov_matrices: List of 4 covariance matrices [V1, V2, V3, V4]
    """
    weights = np.array([w, 1 - w])
    
    # 1. Mixing Law (Equation I.3.102)
    mixing_law = [
        pi_1 * pi_2,
        (1 - pi_1) * pi_2,
        pi_1 * (1 - pi_2),
        (1 - pi_1) * (1 - pi_2)
    ]
    
    component_means = []
    component_variances = []
    
    # 2 & 3. Component Expectations and Variances (Equations I.3.103 & I.3.104)
    for i in range(4):
        mu_i = np.array(mu_vectors[i])
        V_i = np.array(cov_matrices[i])
        
        c_mean = weights.T @ mu_i
        c_var = weights.T @ V_i @ weights
        
        component_means.append(c_mean)
        component_variances.append(c_var)
        
    return mixing_law, component_means, component_variances