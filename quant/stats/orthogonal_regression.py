import numpy as np


def fit_orthogonal_regression(x, y):
    """
    Fits a line using Orthogonal Regression (Total Least Squares) via PCA.
    This minimizes the perpendicular distances to the line, rather than vertical distances.

    Parameters:
    x (numpy.ndarray): 1D array of X data.
    y (numpy.ndarray): 1D array of Y data.

    Returns:
    tuple: (alpha, beta) representing the intercept and slope of the fitted line.
    """
    n = len(x)
    if n != len(y):
        raise ValueError("X and Y arrays must have the same length.")

    # 1. Center the data
    x_mean = np.mean(x)
    y_mean = np.mean(y)

    # Combine into a 2 x n matrix of centered data
    centered_data = np.vstack((x - x_mean, y - y_mean))

    # 2. Compute the 2x2 covariance matrix
    cov_matrix = np.cov(centered_data)

    # 3. Perform Eigen-decomposition
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)

    # The first principal component corresponds to the LARGEST eigenvalue
    # np.linalg.eigh returns eigenvalues in ascending order, so the PC1 is the last column
    pc1_vector = eigenvectors[:, -1]

    # The slope of the orthogonal regression line is the ratio of the y-component to the x-component
    # of the first principal component vector
    beta_orthogonal = pc1_vector[1] / pc1_vector[0]

    # The line passes through the means, so: y_mean = alpha + beta * x_mean
    alpha_orthogonal = y_mean - beta_orthogonal * x_mean

    return alpha_orthogonal, beta_orthogonal


if __name__ == "__main__":
    # --- Example Application ---
    np.random.seed(42)
    x_data = np.random.normal(0, 1, 100)
    y_data = 2.0 * x_data + 1.0 + np.random.normal(0, 0.5, 100)

    # Standard OLS for comparison
    beta_ols = np.cov(x_data, y_data)[0, 1] / np.var(x_data)
    alpha_ols = np.mean(y_data) - beta_ols * np.mean(x_data)

    # Orthogonal Regression
    alpha_orth, beta_orth = fit_orthogonal_regression(x_data, y_data)

    print("--- Regression Comparison ---")
    print(f"OLS:        Alpha = {alpha_ols:.4f}, Beta = {beta_ols:.4f}")
    print(f"Orthogonal: Alpha = {alpha_orth:.4f}, Beta = {beta_orth:.4f}")
    print("(Note: OLS underestimates the true slope of 2.0 due to attenuation bias.)")
