import numpy as np
from scipy.stats import norm, t
from scipy.optimize import brentq

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
        term2 = self.rho * (1 - self.rho**(h_days - 1))
        return h_days + 2 * (self.rho / (1 - self.rho)**2) * (term1 - term2)

    def normal_var(self, h_days: int, alpha: float, autocorrelated: bool = False) -> float:
        h_tilde = self._get_horizon(h_days, autocorrelated)
        spread_var = norm.ppf(1 - alpha) * self.daily_vol * np.sqrt(h_tilde)
        return spread_var * self.pv01

    def student_t_var(self, h_days: int, alpha: float, df: float, autocorrelated: bool = False) -> float:
        h_tilde = self._get_horizon(h_days, autocorrelated)
        # Standardize the t-quantile to assume variance = 1
        t_quant = t.ppf(1 - alpha, df) * np.sqrt((df - 2) / df)
        spread_var = t_quant * self.daily_vol * np.sqrt(h_tilde)
        return spread_var * self.pv01

    def normal_mixture_var(self, h_days: int, alpha: float, pi: float, 
                           vol_1_ratio: float, vol_2_ratio: float, 
                           autocorrelated: bool = False) -> float:
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
print("1. Normal i.i.d.:                   €{:,.0f}".format(
    itraxx_risk.normal_var(horizon, confidence, autocorrelated=False)))

print("2. Normal (Autocorrelated):         €{:,.0f}".format(
    itraxx_risk.normal_var(horizon, confidence, autocorrelated=True)))

print("3. Student-t i.i.d.:                €{:,.0f}".format(
    itraxx_risk.student_t_var(horizon, confidence, t_degrees_of_freedom, autocorrelated=False)))

print("4. Normal Mixture i.i.d.:           €{:,.0f}".format(
    itraxx_risk.normal_mixture_var(horizon, confidence, mix_pi, v_ratio_1, v_ratio_2, False)))

print("5. Normal Mixture (Autocorrelated): €{:,.0f}".format(
    itraxx_risk.normal_mixture_var(horizon, confidence, mix_pi, v_ratio_1, v_ratio_2, True)))

print("-" * 42)
print("Conclusion: The Autocorrelated Normal Mixture captures the 'fat tails' and serial dependence, resulting in a drastically higher, safer capital reserve.")