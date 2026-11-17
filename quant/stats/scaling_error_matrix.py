"""Scaling-error matrix for power-law VaR horizon scaling.

Compares the true h-day scaling multiplier h^c against the naive
square-root-of-time rule h^0.5 for a grid of horizons and scale exponents
(Table IV.3.4). Reference: Alexander (2008), Vol. IV.
"""

import pandas as pd


def generate_scaling_error_matrix(horizons: list, exponents: list, base_exponent: float = 0.5):
    """
    Generates Table IV.3.4: Scaling 1-day VaR for different risk horizons
    and scale exponents relative to the square-root-of-time rule.
    """
    df = pd.DataFrame(index=horizons, columns=exponents)
    df.index.name = "Horizon (days)"

    for h in horizons:
        # The base multiplier if we mistakenly assume normality (c=0.5)
        base_multiplier = h**base_exponent

        for c in exponents:
            # The true multiplier based on the empirical power law
            true_multiplier = h**c

            if c == base_exponent:
                df.loc[h, c] = f"{base_multiplier:.2f}x"
            else:
                # Calculate what percentage the true VaR is compared to the naive Square-Root VaR
                percentage_of_base = true_multiplier / base_multiplier
                df.loc[h, c] = f"{percentage_of_base:.1%}"

    return df


def compute(data, exponents=None, base_exponent=0.5) -> dict:
    """Standard facade: scaling-error matrix as a JSON-serializable dict.

    Parameters:
    data: list of risk horizons in days (positive).
    exponents: list of candidate scale exponents.
    base_exponent (float): exponent of the naive rule (default 0.5).

    Returns:
    dict: {"base_exponent", "matrix": {"<horizon>": {"<exponent>": cell}}};
    the base-exponent column shows the "x" multiplier, other columns the
    percentage of the naive multiplier.
    """
    if exponents is None:
        raise ValueError("exponents is required")
    horizons = [float(h) for h in data]
    exponents = [float(e) for e in exponents]
    if not horizons or not exponents:
        raise ValueError("horizons and exponents must be non-empty")
    if any(h <= 0.0 for h in horizons):
        raise ValueError("horizons must be positive")

    df = generate_scaling_error_matrix(horizons, exponents, float(base_exponent))
    matrix = {
        f"{h:g}": {f"{e:g}": value for e, value in row.items()}
        for h, row in df.to_dict(orient="index").items()
    }
    return {"base_exponent": float(base_exponent), "matrix": matrix}


if __name__ == "__main__":
    # Parameters from Table IV.3.4
    risk_horizons = [2, 5, 10, 30, 100, 250]
    scale_exponents = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]

    error_matrix = generate_scaling_error_matrix(risk_horizons, scale_exponents)

    print("Table IV.3.4: Scaling 1-day VaR for different scale exponents")
    print("-" * 90)
    print(error_matrix.to_string())
    print("-" * 90)
