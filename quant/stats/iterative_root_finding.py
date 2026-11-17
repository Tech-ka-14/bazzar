"""Iterative root finding.

Bisection and Newton-Raphson methods for solving f(x) = 0, applied to
recovering a bond's yield from its market price. Reference: Alexander (2008),
Vol. I, Example I.5.2.
"""


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


def compute(data, coupon=5.0, face_value=100.0, years=4, method="newton_raphson") -> dict:
    """Standard facade: solve a bond's yield from its market price.

    Parameters:
    data (float): observed market price of the bond (positive).
    coupon (float): annual coupon payment.
    face_value (float): redemption value at maturity.
    years (int): years to maturity (>= 1).
    method (str): "newton_raphson" or "bisection".

    Returns:
    dict: {"method", "market_price", "yield"}.
    """
    price = float(data)
    coupon = float(coupon)
    face_value = float(face_value)
    years = int(years)
    if price <= 0.0 or coupon < 0.0 or face_value <= 0.0:
        raise ValueError("price and face_value must be positive; coupon non-negative")
    if years < 1:
        raise ValueError("years must be a positive integer")

    def pricing_error(y):
        present = sum(coupon / (1 + y) ** i for i in range(1, years + 1))
        return present + face_value / (1 + y) ** years - price

    def pricing_derivative(y):
        deriv = sum(-coupon * i / (1 + y) ** (i + 1) for i in range(1, years + 1))
        return deriv - face_value * years / (1 + y) ** (years + 1)

    if method == "newton_raphson":
        estimate = newton_raphson_method(pricing_error, pricing_derivative, x0=0.05)
    elif method == "bisection":
        estimate = bisection_method(pricing_error, 1e-6, 1.0)
    else:
        raise ValueError("method must be 'newton_raphson' or 'bisection'")

    return {"method": method, "market_price": price, "yield": float(estimate)}


if __name__ == "__main__":
    # --- Example I.5.2: Finding a Bond Yield ---
    # 4-year bond, 5% annual coupon, market price = 92

    # Objective function: PV(y) - MarketPrice = 0
    def bond_pricing_error(y):
        cash_flows = sum([5 / (1 + y) ** i for i in range(1, 5)]) + (100 / (1 + y) ** 4)
        return cash_flows - 92.0

    # Derivative of the objective function w.r.t yield (y)
    def bond_pricing_deriv(y):
        deriv = sum([-5 * i / (1 + y) ** (i + 1) for i in range(1, 5)]) - (400 / (1 + y) ** 5)
        return deriv

    # Use Newton-Raphson starting with a guess of 5% (0.05)
    yield_estimate = newton_raphson_method(bond_pricing_error, bond_pricing_deriv, x0=0.05)
    print(f"Estimated Bond Yield: {yield_estimate * 100:.2f}%")
