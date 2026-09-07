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
    # --- Example I.5.2: Finding a Root for f(x) = x^3 - 2x - 5 = 0 ---
    def f(x):
        return x**3 - 2 * x - 5

    def f_prime(x):
        return 3 * x**2 - 2

    # Root lies between 2 and 3 because f(2) = -1 and f(3) = 16
    root_bisect = bisection_method(f, 2, 3)
    root_newton = newton_raphson_method(f, f_prime, x0=2.5)

    print(f"Bisection Method Root: {root_bisect:.6f}")
    print(f"Newton-Raphson Root: {root_newton:.6f}")
