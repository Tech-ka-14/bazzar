import numpy as np

def linear_interpolation(x, x1, y1, x2, y2):
    """
    Performs standard linear interpolation.
    """
    return ((x2 - x) * y1 + (x - x1) * y2) / (x2 - x1)

def fit_quadratic_smile(x_points, y_points):
    """
    Fits a quadratic polynomial f(x) = ax^2 + bx + c through exactly 3 points.
    Returns the coefficients [a, b, c].
    """
    # Create the matrix of x combinations: [x^2, x, 1]
    X_matrix = np.array([
        [x_points[0]**2, x_points[0], 1],
        [x_points[1]**2, x_points[1], 1],
        [x_points[2]**2, x_points[2], 1]
    ])
    
    # Solve for coefficients [a, b, c]
    coefficients = np.linalg.inv(X_matrix) @ y_points
    return coefficients

if __name__ == "__main__":
    # --- Example I.5.5: Fitting a Currency Option Smile ---
    # Given implied vols for 25-delta, 50-delta (ATM), and 75-delta
    deltas = np.array([0.25, 0.50, 0.75])
    vols = np.array([0.205, 0.180, 0.195])
    
    a, b, c = fit_quadratic_smile(deltas, vols)
    
    # Interpolate the 10-delta (0.10) and 90-delta (0.90) volatilities
    vol_10 = a*(0.10**2) + b*(0.10) + c
    vol_90 = a*(0.90**2) + b*(0.90) + c
    
    print("--- Quadratic Volatility Smile Fit ---")
    print(f"Coefficients: a={a:.3f}, b={b:.3f}, c={c:.3f}")
    print(f"Interpolated 10-Delta Volatility: {vol_10 * 100:.2f}%")
    print(f"Interpolated 90-Delta Volatility: {vol_90 * 100:.2f}%")