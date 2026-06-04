import numpy as np

def bisection_method(func, x_lower, x_upper, tol=1e-6, max_iter=100):
    """
    Finds the root of a function using the Method of Bisection.
    """
    if func(x_lower) * func(x_upper) >= 0:
        raise ValueError("Function must have different signs at x_lower and x_upper.")
    
    for _ in range(max_iter):
        x_mid = (x_lower + x_upper) / 2.0
        f_mid = func(x_mid)
        
        if abs(f_mid) < tol:
            return x_mid
            
        if func(x_lower) * f_mid < 0:
            x_upper = x_mid
        else:
            x_lower = x_mid
            
    return (x_lower + x_upper) / 2.0

def newton_raphson_method(func, deriv_func, x0, tol=1e-6, max_iter=100):
    """
    Finds the root of a function using Newton-Raphson iteration.
    """
    x_n = x0
    for _ in range(max_iter):
        f_xn = func(x_n)
        if abs(f_xn) < tol:
            return x_n
        
        f_prime_xn = deriv_func(x_n)
        if f_prime_xn == 0:
            raise ZeroDivisionError("Derivative is zero. Newton-Raphson fails.")
            
        x_n = x_n - (f_xn / f_prime_xn)
        
    return x_n

if __name__ == "__main__":
    # --- Example I.5.2: Finding a Bond Yield ---
    # 4-year bond, 5% annual coupon, market price = 92
    
    # Objective function: PV(y) - MarketPrice = 0
    def bond_pricing_error(y):
        cash_flows = sum([5 / (1 + y)**i for i in range(1, 5)]) + (100 / (1 + y)**4)
        return cash_flows - 92.0
        
    # Derivative of the objective function w.r.t yield (y)
    def bond_pricing_deriv(y):
        deriv = sum([-5 * i / (1 + y)**(i + 1) for i in range(1, 5)]) - (400 / (1 + y)**5)
        return deriv

    # Use Newton-Raphson starting with a guess of 5% (0.05)
    yield_estimate = newton_raphson_method(bond_pricing_error, bond_pricing_deriv, x0=0.05)
    print(f"Estimated Bond Yield: {yield_estimate * 100:.2f}%")