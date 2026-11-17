"""Model-risk comparison of credit-spread VaR models (iTraxx Europe).

Compares normal, autocorrelated normal, Student-t and normal-mixture
parametric VaR models for a credit-spread index position mapped via PV01.
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.2.12.
"""

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm, t


class CreditSpreadVaRModels:
    """
    Consolidated framework for comparing parametric linear VaR models
    on the iTraxx Europe 5-year index.
    """

    def __init__(self, daily_vol_bp: float, autocorrelation: float, pv01_euros: float):
        self.daily_vol = daily_vol_bp
        self.rho = autocorrelation
        self.pv01 = pv01_euros

    def _get_horizon(self, h_days: int, use_autocorrelation: bool) -> float:
        """Calculates h_tilde if autocorrelation is applied, else returns h."""
        if not use_autocorrelation or self.rho == 0:
            return float(h_days)
        term1 = (h_days - 1) * (1 - self.rho)
        term2 = self.rho * (1 - self.rho ** (h_days - 1))
        return h_days + 2 * (self.rho / (1 - self.rho) ** 2) * (term1 - term2)

    def normal_var(self, h_days: int, alpha: float, autocorrelated: bool = False) -> float:
        h_tilde = self._get_horizon(h_days, autocorrelated)
        spread_var = norm.ppf(1 - alpha) * self.daily_vol * np.sqrt(h_tilde)
        return spread_var * self.pv01

    def student_t_var(
        self, h_days: int, alpha: float, df: float, autocorrelated: bool = False
    ) -> float:
        h_tilde = self._get_horizon(h_days, autocorrelated)
        # Standardize the t-quantile to assume variance = 1
        t_quant = t.ppf(1 - alpha, df) * np.sqrt((df - 2) / df)
        spread_var = t_quant * self.daily_vol * np.sqrt(h_tilde)
        return spread_var * self.pv01

    def normal_mixture_var(
        self,
        h_days: int,
        alpha: float,
        pi: float,
        vol_1_ratio: float,
        vol_2_ratio: float,
        autocorrelated: bool = False,
    ) -> float:
        """
        Solves the mixture implicitly. vol_ratios define the regimes relative to base daily_vol.
        """
        h_tilde = self._get_horizon(h_days, autocorrelated)

        # Scale component volatilities to h_tilde
        sigma_1 = self.daily_vol * vol_1_ratio * np.sqrt(h_tilde)
        sigma_2 = self.daily_vol * vol_2_ratio * np.sqrt(h_tilde)

        def mixture_cdf_root(x):
            return (pi * norm.cdf(x / sigma_1)) + ((1 - pi) * norm.cdf(x / sigma_2)) - alpha

        x_alpha = brentq(mixture_cdf_root, -10 * max(sigma_1, sigma_2), 10 * max(sigma_1, sigma_2))
        spread_var = -x_alpha
        return spread_var * self.pv01


# --- Executing the iTraxx Model Risk Case Study ---

# Parameters from Section IV.2.12


def compute(
    daily_vol_bp: float,
    pv01_euros: float,
    autocorrelation: float = 0.0,
    h_days: int = 10,
    alpha: float = 0.01,
    df: float = 4.0,
    mix_pi: float = 0.85,
    vol_1_ratio: float = 0.6,
    vol_2_ratio: float = 2.0,
) -> dict:
    """Standard facade: iTraxx credit-spread VaR model comparison.

    Parameters:
    daily_vol_bp (float): Daily spread volatility in basis points.
    pv01_euros (float): PV01 of the position in euros per basis point.
    autocorrelation (float): AR(1) autocorrelation of spread changes.
    h_days (int): Risk horizon in days.
    alpha (float): Tail probability in (0, 1), e.g. 0.01.
    df (float): Degrees of freedom for the Student-t model (> 2).
    mix_pi (float): Quiet-regime probability of the normal mixture.
    vol_1_ratio, vol_2_ratio (float): Regime volatilities relative to
    daily_vol_bp.

    Returns:
    dict: {"method", "alpha", "h_days", "var_normal",
    "var_normal_autocorrelated", "var_student_t", "var_normal_mixture",
    "var_normal_mixture_autocorrelated"} with positive monetary losses.
    """
    if daily_vol_bp <= 0:
        raise ValueError("daily_vol_bp must be positive")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")
    if df <= 2:
        raise ValueError("df must be greater than 2 for finite variance")
    if not 0.0 < mix_pi < 1.0:
        raise ValueError("mix_pi must be in the open interval (0, 1)")

    models = CreditSpreadVaRModels(float(daily_vol_bp), float(autocorrelation), float(pv01_euros))
    h = int(h_days)
    a = float(alpha)
    return {
        "method": "itraxx_model_comparison",
        "alpha": a,
        "h_days": h,
        "var_normal": float(models.normal_var(h, a, autocorrelated=False)),
        "var_normal_autocorrelated": float(models.normal_var(h, a, autocorrelated=True)),
        "var_student_t": float(models.student_t_var(h, a, float(df), autocorrelated=False)),
        "var_normal_mixture": float(
            models.normal_mixture_var(
                h, a, float(mix_pi), float(vol_1_ratio), float(vol_2_ratio), False
            )
        ),
        "var_normal_mixture_autocorrelated": float(
            models.normal_mixture_var(
                h, a, float(mix_pi), float(vol_1_ratio), float(vol_2_ratio), True
            )
        ),
    }


if __name__ == "__main__":
    daily_volatility_bp = 2.4037
    ar1_coefficient = 0.1079
    portfolio_pv01 = 1000.0  # €1000 per basis point

    # Initialize the calculator
    itraxx_risk = CreditSpreadVaRModels(daily_volatility_bp, ar1_coefficient, portfolio_pv01)

    # VaR Parameters
    horizon = 10
    confidence = 0.01  # 1% VaR

    # Theoretical Mixture Parameters (Proxying the heavy tails mentioned in the text)
    # e.g., 85% chance of a quiet regime (0.6x vol), 15% chance of a crash regime (2.0x vol)
    mix_pi = 0.85
    v_ratio_1 = 0.6
    v_ratio_2 = 2.0
    t_degrees_of_freedom = 4.0

    print("--- iTraxx 1% 10-Day VaR Estimates (€) ---")
    print(
        "1. Normal i.i.d.:                   €{:,.0f}".format(
            itraxx_risk.normal_var(horizon, confidence, autocorrelated=False)
        )
    )

    print(
        "2. Normal (Autocorrelated):         €{:,.0f}".format(
            itraxx_risk.normal_var(horizon, confidence, autocorrelated=True)
        )
    )

    print(
        "3. Student-t i.i.d.:                €{:,.0f}".format(
            itraxx_risk.student_t_var(
                horizon, confidence, t_degrees_of_freedom, autocorrelated=False
            )
        )
    )

    print(
        "4. Normal Mixture i.i.d.:           €{:,.0f}".format(
            itraxx_risk.normal_mixture_var(horizon, confidence, mix_pi, v_ratio_1, v_ratio_2, False)
        )
    )

    print(
        "5. Normal Mixture (Autocorrelated): €{:,.0f}".format(
            itraxx_risk.normal_mixture_var(horizon, confidence, mix_pi, v_ratio_1, v_ratio_2, True)
        )
    )

    print("-" * 42)
    print(
        "Conclusion: The Autocorrelated Normal Mixture captures the 'fat tails' and serial dependence, resulting in a drastically higher, safer capital reserve."
    )
