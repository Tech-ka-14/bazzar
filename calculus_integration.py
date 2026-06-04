import sympy as sp
import scipy.integrate as spi

def symbolic_definite_integral(expression_str, a, b):
    """
    Evaluates a definite integral symbolically using sympy.
    Best for smooth, standard analytical functions.
    """
    x = sp.Symbol('x')
    f_x = sp.sympify(expression_str)
    
    # Evaluate the definite integral F(b) - F(a)
    result = sp.integrate(f_x, (x, a, b))
    
    return float(result.evalf())

def numerical_definite_integral(func, a, b):
    """
    Evaluates a definite integral numerically using scipy.
    Best for programmatic functions or complex pricing models.
    """
    # quad returns the integral value and an estimate of the absolute error
    result, error = spi.quad(func, a, b)
    return result

# --- Testing with Example I.1.4 from the text ---
if __name__ == "__main__":
    # The function from the text: f(x) = 2x + x^2
    expression = "2*x + x**2"
    lower_limit = 2
    upper_limit = 4
    
    # 1. Symbolic approach
    sym_result = symbolic_definite_integral(expression, lower_limit, upper_limit)
    print(f"Symbolic Integral Result: {sym_result:.2f}")
    
    # 2. Numerical approach
    # Define the mathematical function as a Python lambda function
    def f(x):
        return 2*x + x**2
        
    num_result = numerical_definite_integral(f, lower_limit, upper_limit)
    print(f"Numerical Integral Result: {num_result:.2f}")