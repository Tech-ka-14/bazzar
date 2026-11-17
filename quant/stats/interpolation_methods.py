"""Interpolation methods.

Standard linear interpolation and an exact quadratic fit through three
points, as used for volatility smiles. Reference: Alexander (2008), Vol. I,
Example I.5.5.
"""

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
    X_matrix = np.array(
        [
            [x_points[0] ** 2, x_points[0], 1],
            [x_points[1] ** 2, x_points[1], 1],
            [x_points[2] ** 2, x_points[2], 1],
        ]
    )

    # Solve for coefficients [a, b, c]
    coefficients = np.linalg.inv(X_matrix) @ y_points
    return coefficients


def compute(data, y_points=None, x=None) -> dict:
    """Standard facade: interpolate at x from 2 (linear) or 3 (quadratic) points.

    Parameters:
    data: array-like of 2 or 3 x-coordinates of the known points.
    y_points: array-like of the corresponding y values.
    x (float): evaluation point.

    Returns:
    dict: {"method", "x", "value"} plus {"coefficients": [a, b, c]} for the
    quadratic fit.
    """
    if y_points is None or x is None:
        raise ValueError("y_points and x are required")
    xs = np.asarray(data, dtype=float).ravel()
    ys = np.asarray(y_points, dtype=float).ravel()
    if xs.shape != ys.shape:
        raise ValueError("data and y_points must have equal length")
    x = float(x)

    if xs.size == 2:
        value = linear_interpolation(x, xs[0], ys[0], xs[1], ys[1])
        return {"method": "linear", "x": x, "value": float(value)}
    if xs.size == 3:
        a, b, c = fit_quadratic_smile(xs, ys)
        return {
            "method": "quadratic",
            "x": x,
            "value": float(a * x**2 + b * x + c),
            "coefficients": [float(a), float(b), float(c)],
        }
    raise ValueError("exactly 2 (linear) or 3 (quadratic) points are supported")


if __name__ == "__main__":
    # --- Example I.5.5: Fitting a Currency Option Smile ---
    # Given implied vols for 25-delta, 50-delta (ATM), and 75-delta
    deltas = np.array([0.25, 0.50, 0.75])
    vols = np.array([0.205, 0.180, 0.195])

    a, b, c = fit_quadratic_smile(deltas, vols)

    # Interpolate the 10-delta (0.10) and 90-delta (0.90) volatilities
    vol_10 = a * (0.10**2) + b * (0.10) + c
    vol_90 = a * (0.90**2) + b * (0.90) + c

    print("--- Quadratic Volatility Smile Fit ---")
    print(f"Coefficients: a={a:.3f}, b={b:.3f}, c={c:.3f}")
    print(f"Interpolated 10-Delta Volatility: {vol_10 * 100:.2f}%")
    print(f"Interpolated 90-Delta Volatility: {vol_90 * 100:.2f}%")
