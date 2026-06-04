import numpy as np
import scipy.stats as stats

def durbin_watson_test(residuals):
    """
    Calculates the Durbin-Watson statistic for autocorrelation.
    """
    diff_res = np.diff(residuals, axis=0)
    dw_stat = np.sum(diff_res**2) / np.sum(residuals**2)
    return dw_stat

def whites_heteroscedasticity_test(X, residuals):
    """
    Performs White's Test for Heteroscedasticity.
    Note: X should include the constant term.
    """
    T, k = X.shape
    e_sq = residuals ** 2
    
    # Build auxiliary explanatory variables: original, squares, and cross-products
    # For simplicity in this functional code, we will assume a 2-variable model (Constant, X1, X2)
    # as demonstrated in Example I.4.13.
    
    # Create auxiliary matrix (excluding the constant to avoid dummy variable trap during cross products)
    X_vars = X[:, 1:] 
    num_vars = X_vars.shape[1]
    
    aux_features = [np.ones((T, 1))]  # Start with constant
    
    # 1. Original variables
    for i in range(num_vars):
        aux_features.append(X_vars[:, i:i+1])
        
    # 2. Squared variables
    for i in range(num_vars):
        aux_features.append(X_vars[:, i:i+1] ** 2)
        
    # 3. Cross products
    for i in range(num_vars):
        for j in range(i + 1, num_vars):
            aux_features.append(X_vars[:, i:i+1] * X_vars[:, j:j+1])
            
    Z = np.column_stack(aux_features)
    
    # Perform auxiliary OLS regression: e^2 on Z
    Z_inv = np.linalg.inv(Z.T @ Z)
    gamma_hat = Z_inv @ Z.T @ e_sq
    e_sq_hat = Z @ gamma_hat
    
    # Calculate R-squared of the auxiliary regression
    TSS = np.sum((e_sq - np.mean(e_sq))**2)
    RSS = np.sum((e_sq - e_sq_hat)**2)
    R_sq_aux = 1 - (RSS / TSS)
    
    # Calculate test statistic
    test_statistic = T * R_sq_aux
    degrees_of_freedom = Z.shape[1] - 1  # Excluding constant
    p_value = 1 - stats.chi2.cdf(test_statistic, degrees_of_freedom)
    
    return test_statistic, p_value, degrees_of_freedom

if __name__ == "__main__":
    # Example I.4.12 & I.4.13 implementation using synthetic data mimicking the Billiton regression
    np.random.seed(42)
    T = 600
    residuals = np.random.normal(0, 1, T)
    
    # 1. Durbin-Watson Test
    dw = durbin_watson_test(residuals)
    print(f"Durbin-Watson Statistic: {dw:.3f} (Close to 2 = No strong autocorrelation)")
    
    # 2. White's Test
    # X matrix with Constant, Gold Return, Oil Return
    X_matrix = np.column_stack((np.ones(T), np.random.normal(0, 0.05, T), np.random.normal(0, 0.05, T)))
    test_stat, p_val, df = whites_heteroscedasticity_test(X_matrix, residuals)
    
    print("\nWhite's Test for Heteroscedasticity:")
    print(f"Test Statistic (T*R^2): {test_stat:.2f}")
    print(f"Degrees of Freedom: {df}")
    print(f"P-Value: {p_val:.4f}")