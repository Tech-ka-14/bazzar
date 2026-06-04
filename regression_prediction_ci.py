import numpy as np
import scipy.stats as stats

def prediction_confidence_interval(x_0, beta_hat, s_squared, XX_inv, df, confidence_level=0.90):
    """
    Calculates the point prediction and its confidence interval for a multivariate regression.
    
    Parameters:
    x_0 (numpy.ndarray): The vector of specific values for explanatory variables (including constant).
    beta_hat (numpy.ndarray): The estimated coefficients vector.
    s_squared (float): The estimated variance of the regression error (residuals variance).
    XX_inv (numpy.ndarray): The inverse matrix (X'X)^-1.
    df (int): Degrees of freedom (T - k).
    confidence_level (float): The desired confidence level.
    
    Returns:
    tuple: (point_prediction, lower_bound, upper_bound, standard_error)
    """
    # 1. Calculate the point prediction (Best Linear Unbiased Predictor)
    y_hat_0 = x_0.T @ beta_hat
    
    # 2. Calculate the variance of the prediction error
    # Formula: s^2 * (1 + x_0' * (X'X)^-1 * x_0)
    variance_mean_prediction = x_0.T @ XX_inv @ x_0
    var_pred_error = s_squared * (1 + variance_mean_prediction)
    
    # 3. Calculate the standard error of the prediction
    se_pred = np.sqrt(var_pred_error)
    
    # 4. Calculate the confidence interval
    alpha = 1.0 - confidence_level
    q = 1.0 - (alpha / 2.0)
    t_critical = stats.t.ppf(q, df)
    
    margin_of_error = t_critical * se_pred
    lower_bound = y_hat_0 - margin_of_error
    upper_bound = y_hat_0 + margin_of_error
    
    return float(y_hat_0), float(lower_bound), float(upper_bound), float(se_pred)

# --- Example I.4.11 Implementation ---
if __name__ == "__main__":
    # Scenario: Intercept=1, Gold falls 10% (-0.1), Oil falls 20% (-0.2)
    x_scenario = np.array([1, -0.1, -0.2])
    
    # Estimated coefficients [Constant, Gold, Oil]
    beta = np.array([0.0025, 0.1709, 0.5969])
    
    # Model parameters
    residual_variance = 0.00143  # s^2
    degrees_of_freedom = 569     # from previous context
    
    # Matrix (X'X)^-1
    XX_inverse = np.array([
        [0.0252, -0.0144, -0.0716],
        [-0.0144, 8.82239, -4.89593],
        [-0.0716, -4.89593, 31.5022]
    ])
    
    prediction, lower, upper, standard_error = prediction_confidence_interval(
        x_scenario, beta, residual_variance, XX_inverse, degrees_of_freedom, confidence_level=0.90
    )
    
    print(f"Point Prediction: {prediction * 100:.2f}%")
    print(f"Prediction Standard Error: {standard_error:.4f}")
    print(f"90% Confidence Interval: [{lower * 100:.2f}%, {upper * 100:.2f}%]")