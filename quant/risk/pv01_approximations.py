"""Exact and approximate PV01 of a single cash flow.

Exact discrete-compounding PV01 (bump and reprice) and analytical
approximations under discrete and continuous compounding.
Reference: Alexander (2008), Market Risk Analysis IV, Equations
IV.2.27-IV.2.30, Example IV.2.4.
"""

import numpy as np


def pv01_exact_discrete(cash_flow: float, rate: float, maturity_years: float) -> float:
    """Calculates exact PV01 using discrete compounding (Equation IV.2.27)."""
    pv_base = cash_flow / ((1 + rate) ** maturity_years)
    pv_down = cash_flow / ((1 + (rate - 0.0001)) ** maturity_years)
    return pv_down - pv_base


def pv01_approx_discrete(cash_flow: float, rate: float, maturity_years: float) -> float:
    """Calculates an analytical approximation of PV01 (Equation IV.2.28)."""
    return maturity_years * cash_flow * ((1 + rate) ** -(maturity_years + 1)) * 1e-4


def pv01_approx_continuous(cash_flow: float, rate: float, maturity_years: float) -> float:
    """Calculates PV01 approximation assuming continuous compounding (Equation IV.2.30)."""
    return maturity_years * cash_flow * np.exp(-rate * maturity_years) * 1e-4


# Example IV.2.4: Finding PV01 for a Swap's Year-1 Cash Flow


def compute(cash_flow: float, rate: float, maturity_years: float) -> dict:
    """Standard facade: exact and approximate PV01 as a JSON-serializable dict.

    Parameters:
    cash_flow (float): Cash flow amount at maturity.
    rate (float): Interest rate as a fraction (e.g. 0.04).
    maturity_years (float): Time to the cash flow in years (positive).

    Returns:
    dict: {"method", "pv01_exact_discrete", "pv01_approx_discrete",
    "pv01_approx_continuous"}.
    """
    if maturity_years <= 0:
        raise ValueError("maturity_years must be positive")

    exact = pv01_exact_discrete(float(cash_flow), float(rate), float(maturity_years))
    approx_d = pv01_approx_discrete(float(cash_flow), float(rate), float(maturity_years))
    approx_c = pv01_approx_continuous(float(cash_flow), float(rate), float(maturity_years))
    return {
        "method": "pv01",
        "pv01_exact_discrete": float(exact),
        "pv01_approx_discrete": float(approx_d),
        "pv01_approx_continuous": float(approx_c),
    }


if __name__ == "__main__":
    c_1 = 3_000_000  # $3 million cash flow in Year 1
    r_1 = 0.04  # 4% interest rate

    exact_val = pv01_exact_discrete(c_1, r_1, 1)
    approx_disc = pv01_approx_discrete(c_1, r_1, 1)

    print(f"Exact PV01 (Discrete): ${exact_val:.4f}")
    print(f"Approx PV01 (Discrete): ${approx_disc:.4f}")
