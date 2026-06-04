import numpy as np

def calculate_bivariate_statistics(x_values, y_values, joint_probabilities):
    """
    Calculates marginal expectations, variance, covariance, and correlation 
    from a discrete bivariate probability distribution.
    """
    P = np.array(joint_probabilities)
    X = np.array(x_values)
    Y = np.array(y_values)
    
    # 1. Marginal Probabilities (Summing across rows/cols)
    P_X = np.sum(P, axis=0) # Sum over Y
    P_Y = np.sum(P, axis=1) # Sum over X
    
    # 2. Marginal Expectations: E(X) and E(Y)
    mu_X = np.sum(X * P_X)
    mu_Y = np.sum(Y * P_Y)
    
    # 3. Variances: E(X^2) - E(X)^2
    var_X = np.sum((X**2) * P_X) - (mu_X**2)
    var_Y = np.sum((Y**2) * P_Y) - (mu_Y**2)
    
    # 4. Covariance: E(XY) - E(X)E(Y)
    # E(XY) is calculated by creating a grid of X*Y and multiplying by joint probabilities
    X_grid, Y_grid = np.meshgrid(X, Y)
    E_XY = np.sum(X_grid * Y_grid * P)
    
    covariance = E_XY - (mu_X * mu_Y)
    
    # 5. Correlation: Cov(X,Y) / (Std(X)*Std(Y))
    correlation = covariance / np.sqrt(var_X * var_Y)
    
    print(f"Expectations -> E(X): {mu_X:.2f}, E(Y): {mu_Y:.2f}")
    print(f"Variances -> V(X): {var_X:.2f}, V(Y): {var_Y:.2f}")
    print(f"Covariance: {covariance:.2f}")
    print(f"Correlation: {correlation:.4f}")
    
    return mu_X, mu_Y, var_X, var_Y, covariance, correlation

# --- Testing with Examples I.3.10 and I.3.11 from the text ---
if __name__ == "__main__":
    print("--- Example I.3.10 & I.3.11: Bivariate Statistics ---")
    x_vals = [-20, -10, 5, 10, 20]
    y_vals = [0, -20, 40, 30, -10]
    
    # Joint probabilities matching Table I.3.6
    # Note: The table maps specific (x,y) pairs. To represent this as a matrix,
    # we place the probabilities where X and Y intersect, and 0 elsewhere.
    joint_prob_matrix = np.zeros((len(y_vals), len(x_vals)))
    # P(X=-20, Y=0) = 0.2
    joint_prob_matrix[0, 0] = 0.2
    # P(X=-10, Y=-20) = 0.1
    joint_prob_matrix[1, 1] = 0.1
    # P(X=5, Y=40) = 0.3
    joint_prob_matrix[2, 2] = 0.3
    # P(X=10, Y=30) = 0.25
    joint_prob_matrix[3, 3] = 0.25
    # P(X=20, Y=-10) = 0.15
    joint_prob_matrix[4, 4] = 0.15
    
    calculate_bivariate_statistics(x_vals, y_vals, joint_prob_matrix)