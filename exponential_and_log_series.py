import math

def exp_power_series(x, num_terms=10):
    """
    Approximates exp(x) using the power series expansion:
    exp(x) = 1 + x + x^2/2! + x^3/3! + ...
    """
    result = 0
    for n in range(num_terms):
        result += (x**n) / math.factorial(n)
    return result

def ln_power_series(x, num_terms=10):
    """
    Approximates ln(1+x) using the power series expansion:
    ln(1+x) = x - x^2/2 + x^3/3 - x^4/4 + ...
    Valid only for -1 < x <= 1.
    """
    if x <= -1 or x > 1:
        raise ValueError("For convergence, x must be strictly between -1 (exclusive) and 1 (inclusive).")
    
    result = 0
    for n in range(1, num_terms + 1):
        term = ((-1)**(n - 1) * x**n) / n
        result += term
    return result

def simple_ln_approximation(x):
    """
    Provides the simple linear approximation ln(1+x) ≈ x for very small x.
    """
    return x

# --- Testing with examples from the text ---
if __name__ == "__main__":
    # Approximating e = exp(1) with 5 terms (0 to 4): 1 + 1 + 1/2 + 1/6 + 1/24
    e_approx = exp_power_series(1, num_terms=5)
    print(f"Approximation of exp(1) with 5 terms: {e_approx:.3f}")
    
    # Approximating exp(2) with 6 terms
    exp2_approx = exp_power_series(2, num_terms=6)
    print(f"Approximation of exp(2) with 6 terms: {exp2_approx:.3f}")

    # Approximating ln(1.1) -> where x = 0.1
    ln_approx = ln_power_series(0.1, num_terms=5)
    print(f"Approximation of ln(1.1) with power series: {ln_approx:.5f}")
    print(f"Linear approximation of ln(1.1): {simple_ln_approximation(0.1):.5f}")