"""Roots of a quadratic equation.

Solves ax^2 + bx + c = 0, returning complex roots via cmath when the
discriminant is negative. Reference: Alexander (2008), Vol. I, Example I.1.1.
"""

import cmath


def solve_quadratic(a, b, c):
    """
    Calculates the roots of a quadratic equation: ax^2 + bx + c = 0.
    Utilizes cmath to safely handle complex roots when the discriminant is negative.
    """
    if a == 0:
        raise ValueError("Coefficient 'a' cannot be zero for a quadratic equation.")

    # Calculate the discriminant
    discriminant = b**2 - 4 * a * c

    # Calculate the two roots
    root1 = (-b + cmath.sqrt(discriminant)) / (2 * a)
    root2 = (-b - cmath.sqrt(discriminant)) / (2 * a)

    # Clean up output if roots are purely real
    if discriminant >= 0:
        return root1.real, root2.real

    return root1, root2


def compute(data, b=0.0, c=0.0) -> dict:
    """Standard facade: quadratic roots as a JSON-serializable dict.

    Parameters:
    data (float): coefficient a of x^2 (non-zero).
    b, c (float): remaining coefficients.

    Returns:
    dict: {"discriminant", "real", "root1", "root2"} when the roots are
    real, otherwise {"discriminant", "real", "root1_real", "root1_imag",
    "root2_real", "root2_imag"}.
    """
    a = float(data)
    b = float(b)
    c = float(c)
    if a == 0.0:
        raise ValueError("coefficient 'a' cannot be zero for a quadratic equation")

    root1, root2 = solve_quadratic(a, b, c)
    discriminant = b**2 - 4 * a * c
    if discriminant >= 0:
        return {
            "discriminant": float(discriminant),
            "real": True,
            "root1": float(root1),
            "root2": float(root2),
        }
    return {
        "discriminant": float(discriminant),
        "real": False,
        "root1_real": float(root1.real),
        "root1_imag": float(root1.imag),
        "root2_real": float(root2.real),
        "root2_imag": float(root2.imag),
    }


# --- Testing with Example I.1.1 from the text ---
if __name__ == "__main__":
    # x^2 - 3x + 2 = 0
    a, b, c = 1, -3, 2
    roots = solve_quadratic(a, b, c)
    print(f"The roots of {a}x^2 + {b}x + {c} = 0 are: {roots}")
