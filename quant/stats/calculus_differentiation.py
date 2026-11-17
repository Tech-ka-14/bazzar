"""Symbolic differentiation and stationary-point analysis.

Differentiates a function string with sympy and classifies its stationary
points via the second-derivative test. Reference: Alexander (2008), Vol. I,
Examples I.1.2-I.1.3.
"""

import sympy as sp


def analyze_function(expression_str):
    """
    Takes a mathematical function as a string, computes its first and second
    derivatives, and identifies any stationary points and their nature
    (maximum, minimum, or saddle point).
    """
    x = sp.Symbol("x", real=True)

    # Parse the string into a sympy expression
    # Note: 'log' in sympy is the natural logarithm (ln)
    f_x = sp.sympify(expression_str)

    # Calculate first and second derivatives
    f_prime = sp.diff(f_x, x)
    f_double_prime = sp.diff(f_prime, x)

    print(f"Function f(x): {f_x}")
    print(f"First Derivative f'(x): {f_prime}")
    print(f"Second Derivative f''(x): {f_double_prime}")

    # Find stationary points where f'(x) = 0
    # Using solve to find exact roots
    stationary_points = sp.solve(f_prime, x)

    print("\n--- Stationary Points Analysis ---")
    if not stationary_points:
        print("No real stationary points found.")
        return

    for point in stationary_points:
        # Evaluate second derivative at the stationary point
        # We use 'N()' to get the numerical value if it's a symbolic fraction/irrational
        eval_2nd_deriv = f_double_prime.subs(x, point).evalf()

        point_val = sp.N(point)

        if eval_2nd_deriv < 0:
            nature = "Local Maximum"
        elif eval_2nd_deriv > 0:
            nature = "Local Minimum"
        else:
            nature = "Saddle Point / Inconclusive (Requires further check)"

        print(f"x = {point_val:.4f} | f''(x) = {eval_2nd_deriv:.4f} -> {nature}")


def compute(data) -> dict:
    """Standard facade: derivatives and stationary points as a JSON dict.

    Parameters:
    data (str): function of x, e.g. "x**3 - 7*x**2 + 14*x - 8"
    (``log`` is the natural logarithm).

    Returns:
    dict: {"function", "first_derivative", "second_derivative",
    "stationary_points": [{"x", "second_derivative", "nature"}]}.
    Complex stationary points are excluded.
    """
    x = sp.Symbol("x", real=True)
    f_x = sp.sympify(data)
    f_prime = sp.diff(f_x, x)
    f_double_prime = sp.diff(f_prime, x)

    stationary_points = []
    for point in sp.solve(f_prime, x):
        point_val = complex(sp.N(point))
        if abs(point_val.imag) > 1e-9:
            continue
        second = float(f_double_prime.subs(x, point).evalf())
        if second < 0:
            nature = "local_maximum"
        elif second > 0:
            nature = "local_minimum"
        else:
            nature = "inconclusive"
        stationary_points.append(
            {"x": point_val.real, "second_derivative": second, "nature": nature}
        )

    return {
        "function": str(f_x),
        "first_derivative": str(f_prime),
        "second_derivative": str(f_double_prime),
        "stationary_points": stationary_points,
    }


# --- Testing with examples from the text ---
if __name__ == "__main__":
    # Example I.1.2 (a): Cubic polynomial
    print("Example I.1.2 (a):")
    analyze_function("x**3 - 7*x**2 + 14*x - 8")

    print("\n" + "=" * 40 + "\n")

    # Example I.1.3: x^2 * ln(x)
    # Note: The text restricts x > 0. Sympy handles this contextually well.
    print("Example I.1.3:")
    analyze_function("x**2 * log(x)")
