"""Normal-mixture VaR of a linear portfolio mapped to two risk factors.

The h-day portfolio return is a four-component normal mixture; VaR is the
negative of the alpha-quantile of the mixture distribution, solved
numerically from the mixture CDF.
Reference: Alexander (2008), Market Risk Analysis IV, Equations
IV.2.75-IV.2.77, Example IV.2.24.
"""

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm


def calculate_bivariate_mixture_var(
    pi_1: float,
    mu_11: float,
    mu_12: float,
    sigma_11: float,
    sigma_12: float,
    pi_2: float,
    mu_21: float,
    mu_22: float,
    sigma_21: float,
    sigma_22: float,
    rho_1: float,
    rho_2: float,
    rho_3: float,
    rho_4: float,
    theta: np.ndarray,
    alpha: float = 0.01,
    h_days: int = 10,
    days_in_year: int = 250,
):
    """
    Calculates the VaR of a linear portfolio mapped to two Normal-Mixture Risk Factors.
    Follows Equations IV.2.75 through IV.2.77.
    """
    # 1. Define the Mixing Law (Probabilities of the 4 combined regimes)
    weights = np.array([pi_1 * pi_2, (1 - pi_1) * pi_2, pi_1 * (1 - pi_2), (1 - pi_1) * (1 - pi_2)])

    # 2. Define the Mean Vectors for the 4 regimes
    mu_vectors = [
        np.array([mu_11, mu_21]),
        np.array([mu_12, mu_21]),
        np.array([mu_11, mu_22]),
        np.array([mu_12, mu_22]),
    ]

    # 3. Define the Covariance Matrices for the 4 regimes
    omega_matrices = [
        np.array(
            [[sigma_11**2, rho_1 * sigma_11 * sigma_21], [rho_1 * sigma_11 * sigma_21, sigma_21**2]]
        ),
        np.array(
            [[sigma_12**2, rho_2 * sigma_12 * sigma_21], [rho_2 * sigma_12 * sigma_21, sigma_21**2]]
        ),
        np.array(
            [[sigma_11**2, rho_3 * sigma_11 * sigma_22], [rho_3 * sigma_11 * sigma_22, sigma_22**2]]
        ),
        np.array(
            [[sigma_12**2, rho_4 * sigma_12 * sigma_22], [rho_4 * sigma_12 * sigma_22, sigma_22**2]]
        ),
    ]

    # 4. Project onto the Portfolio Sensitivity Vector (theta) to get component Means and Variances
    time_scale = h_days / days_in_year

    port_means_h = []
    port_vols_h = []

    for i in range(4):
        # Calculate annualized portfolio mean and variance for component i
        annual_mean = theta.T @ mu_vectors[i]
        annual_var = theta.T @ omega_matrices[i] @ theta

        # Scale to h-day risk horizon
        port_means_h.append(annual_mean * time_scale)
        port_vols_h.append(np.sqrt(annual_var * time_scale))

    port_means_h = np.array(port_means_h)
    port_vols_h = np.array(port_vols_h)

    # 5. Define the implicit Mixture CDF and solve for VaR
    def mixture_cdf_root(x):
        # Probability weighted sum of the 4 Normal CDFs - alpha = 0
        cdf_sum = 0
        for i in range(4):
            cdf_sum += weights[i] * norm.cdf((x - port_means_h[i]) / port_vols_h[i])
        return cdf_sum - alpha

    # Bracket the root finding algorithm securely around the max possible volatility
    max_vol = np.max(port_vols_h)
    min_mean = np.min(port_means_h)

    lower_bound = min_mean - (10 * max_vol)
    upper_bound = np.max(port_means_h) + (10 * max_vol)

    x_alpha = brentq(mixture_cdf_root, lower_bound, upper_bound)

    # VaR is the negative of the loss quantile
    return -x_alpha


# Example IV.2.24: Normal Mixture VaR - Risk Factor Level
# Defining the parameters from Table IV.2.30


def compute(theta, pi, mu, sigma, rho, alpha: float = 0.01, h_days: int = 10) -> dict:
    """Standard facade: bivariate normal-mixture VaR as a JSON-serializable dict.

    Parameters:
    theta: Array-like of 2 portfolio sensitivities to the risk factors.
    pi: (pi_1, pi_2) tail-regime probabilities of the two risk factors.
    mu: (mu_11, mu_12, mu_21, mu_22) tail/core means of factors 1 and 2.
    sigma: (sigma_11, sigma_12, sigma_21, sigma_22) tail/core vols.
    rho: (rho_1, rho_2, rho_3, rho_4) cross-correlations per joint regime.
    alpha (float): Tail probability in (0, 1), e.g. 0.01.
    h_days (int): Risk horizon in days.

    Returns:
    dict: {"method", "alpha", "h_days", "var"} where "var" is the
    positive loss fraction.
    """
    theta = np.asarray(theta, dtype=float).ravel()
    if theta.size != 2:
        raise ValueError("theta must contain exactly 2 sensitivities")
    if len(pi) != 2 or len(mu) != 4 or len(sigma) != 4 or len(rho) != 4:
        raise ValueError("pi must have 2, mu/sigma/rho must have 4 entries each")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    pi_1, pi_2 = (float(x) for x in pi)
    mu_11, mu_12, mu_21, mu_22 = (float(x) for x in mu)
    s11, s12, s21, s22 = (float(x) for x in sigma)
    r1, r2, r3, r4 = (float(x) for x in rho)

    var = calculate_bivariate_mixture_var(
        pi_1,
        mu_11,
        mu_12,
        s11,
        s12,
        pi_2,
        mu_21,
        mu_22,
        s21,
        s22,
        r1,
        r2,
        r3,
        r4,
        theta=theta,
        alpha=float(alpha),
        h_days=int(h_days),
    )
    return {
        "method": "normal_mixture",
        "alpha": float(alpha),
        "h_days": int(h_days),
        "var": float(var),
    }


if __name__ == "__main__":
    theta_vec = np.array([0.8, 1.0])

    # Risk Factor 1 (Tail / Core)
    pi1 = 0.02
    mu11, mu12 = -3.00, 0.02
    sig11, sig12 = 0.75, 0.15

    # Risk Factor 2 (Tail / Core)
    pi2 = 0.03
    mu21, mu22 = -2.00, 0.025
    sig21, sig22 = 0.65, 0.18

    # Cross-correlations
    r1, r2, r3, r4 = 0.30, 0.0, 0.0, 0.80

    var_10d = calculate_bivariate_mixture_var(
        pi1,
        mu11,
        mu12,
        sig11,
        sig12,
        pi2,
        mu21,
        mu22,
        sig21,
        sig22,
        r1,
        r2,
        r3,
        r4,
        theta=theta_vec,
        alpha=0.01,
        h_days=10,
    )

    print(f"1% 10-day Normal Mixture VaR (4-Component Portfolio): {var_10d:.2%}")
