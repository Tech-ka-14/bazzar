import numpy as np

def scale_covariance_matrix(V_1, h):
    """
    Scales a 1-period covariance matrix to an h-period forecast.
    
    Parameters:
    V_1 (numpy.ndarray): The 1-period covariance matrix (n x n).
    h (int): The number of periods.
    
    Returns:
    numpy.ndarray: The h-period covariance matrix.
    """
    return V_1 * h

if __name__ == "__main__":
    # --- Example II.3.14 Implementation ---
    # Daily covariance matrix V_1
    V_1 = np.array([
        [21.644, 6.196],
        [6.196, 7.006]
    ]) * 1e-4
    
    # 5-day forecast
    h = 5
    V_h = scale_covariance_matrix(V_1, h)
    
    print("--- Covariance Matrix Scaling ---")
    print("1-Day Covariance Matrix:")
    print(V_1)
    print("\n5-Day Covariance Matrix Forecast:")
    print(V_h)