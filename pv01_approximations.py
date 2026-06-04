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
c_1 = 3_000_000   # $3 million cash flow in Year 1
r_1 = 0.04        # 4% interest rate

exact_val = pv01_exact_discrete(c_1, r_1, 1)
approx_disc = pv01_approx_discrete(c_1, r_1, 1)

print(f"Exact PV01 (Discrete): ${exact_val:.4f}")
print(f"Approx PV01 (Discrete): ${approx_disc:.4f}")