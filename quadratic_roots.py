import cmath

def solve_quadratic(a, b, c):
    """
    Calculates the roots of a quadratic equation: ax^2 + bx + c = 0.
    Utilizes cmath to safely handle complex roots when the discriminant is negative.
    """
    if a == 0:
        raise ValueError("Coefficient 'a' cannot be zero for a quadratic equation.")

    # Calculate the discriminant
    discriminant = b**2 - 4*a*c
    
    # Calculate the two roots
    root1 = (-b + cmath.sqrt(discriminant)) / (2*a)
    root2 = (-b - cmath.sqrt(discriminant)) / (2*a)
    
    # Clean up output if roots are purely real
    if discriminant >= 0:
        return root1.real, root2.real
    
    return root1, root2

# --- Testing with Example I.1.1 from the text ---
if __name__ == "__main__":
    # x^2 - 3x + 2 = 0
    a, b, c = 1, -3, 2
    roots = solve_quadratic(a, b, c)
    print(f"The roots of {a}x^2 + {b}x + {c} = 0 are: {roots}")