"""Taylor series expansion of a function.

n-th order Taylor polynomial of an expression around a point, computed with
sympy's series expansion. Reference: Alexander (2008), Vol. I,
Example I.1.11.
"""

import sympy as sp


def calculate_taylor_expansion(expression_str, point, order):
    """
    Calculates the n-th order Taylor expansion of a function around a given point x0.

    :param expression_str: The mathematical function as a string (e.g., 'x**3 - 2*log(x)')
    :param point: The point x0 to expand around
    :param order: The degree of the Taylor polynomial (n)
    """
    x = sp.Symbol("x")
    f_x = sp.sympify(expression_str)

    # Sympy's series function computes the Taylor/Laurent series.
    # The 'n' parameter in sympy.series represents the Big-O term,
    # so we use order + 1 to get the polynomial up to the requested degree.
    taylor_series = sp.series(f_x, x, point, order + 1)

    # Remove the Big-O error term (O(x^n)) to leave just the polynomial
    taylor_poly = taylor_series.removeO()

    print(f"Original Function f(x): {f_x}")
    print(f"Taylor Expansion (Order {order}) around x={point}:")
    print(taylor_poly)

    return taylor_poly


def compute(data, point=0.0, order=3) -> dict:
    """Standard facade: Taylor expansion as a JSON-serializable dict.

    Parameters:
    data (str): function of x, e.g. "x**3 - 2*log(x)" (``log`` is ln).
    point (float): expansion point x0.
    order (int): degree of the Taylor polynomial (>= 1).

    Returns:
    dict: {"function", "point", "order", "expansion"} with the polynomial
    rendered as a string.
    """
    if int(order) < 1:
        raise ValueError("order must be a positive integer")

    x = sp.Symbol("x")
    f_x = sp.sympify(data)
    taylor_series = sp.series(f_x, x, float(point), int(order) + 1)
    taylor_poly = taylor_series.removeO()
    return {
        "function": str(f_x),
        "point": float(point),
        "order": int(order),
        "expansion": str(taylor_poly),
    }


# --- Testing with Example I.1.11 from the text ---
if __name__ == "__main__":
    # Function: f(x) = x^3 - 2*ln(x)
    # Note: 'log' in sympy defaults to the natural logarithm (ln)
    expression = "x**3 - 2*log(x)"

    # Expanding around x = 1 up to the 3rd order
    approx_poly = calculate_taylor_expansion(expression, point=1, order=3)

    # We can also evaluate it at a nearby point, e.g., x = 1.02
    x = sp.Symbol("x")
    exact_val = sp.sympify(expression).subs(x, 1.02).evalf()
    approx_val = approx_poly.subs(x, 1.02).evalf()

    print("\nEvaluation at x = 1.02:")
    print(f"Exact Value: {exact_val:.6f}")
    print(f"Approximated Value: {approx_val:.6f}")
