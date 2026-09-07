import numpy as np


def simple_linear_regression(x_data, y_data):
    """
    Fits a simple linear regression line Y = alpha + beta*X + error
    using Ordinary Least Squares (OLS) matrix algebra.

    Parameters:
    x_data : list or 1D numpy array of independent variable observations
    y_data : list or 1D numpy array of dependent variable observations
    """
    n = len(x_data)

    # 1. Setup the Design Matrix X (n x 2)
    # Column 1 is all 1s (for the intercept/alpha), Column 2 is the x data
    X = np.column_stack((np.ones(n), x_data))

    # Convert y_data to a column vector (n x 1)
    y = np.array(y_data).reshape(n, 1)

    # 2. Calculate the OLS Estimator: beta_hat = (X'X)^-1 X'y
    # X' is the transpose of X
    X_prime_X = X.T @ X
    X_prime_X_inv = np.linalg.inv(X_prime_X)
    X_prime_y = X.T @ y

    # beta_hat contains [alpha_hat, beta_hat]
    beta_hat = X_prime_X_inv @ X_prime_y

    alpha_hat = beta_hat[0, 0]
    beta_hat_val = beta_hat[1, 0]

    # 3. Calculate Residuals and Sum of Squared Errors (RSS)
    # y_hat = X * beta_hat
    y_hat = X @ beta_hat

    # residuals e = y - y_hat
    residuals = y - y_hat

    # RSS = e'e (sum of squared residuals)
    rss = (residuals.T @ residuals)[0, 0]

    print(f"--- OLS Regression Results ---")
    print(f"Estimated Intercept (alpha): {alpha_hat:.4f}")
    print(f"Estimated Slope (beta):      {beta_hat_val:.4f}")
    print(f"Residual Sum of Squares (RSS): {rss:.4f}")

    return alpha_hat, beta_hat_val, rss


# --- Testing with the concept from the text ---
if __name__ == "__main__":
    # Hypothetical data (e.g., advertising spend vs sales)
    X_observed = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    Y_observed = [2.1, 4.3, 5.8, 8.2, 9.9, 12.5, 13.8, 16.4, 18.1, 20.5]

    simple_linear_regression(X_observed, Y_observed)
