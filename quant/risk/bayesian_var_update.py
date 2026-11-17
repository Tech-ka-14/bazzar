"""Bayesian posterior VaR combining data likelihood with a prior.

The posterior normal parameters are the precision-weighted combination of
the likelihood and prior moments; VaR is then computed from the posterior
normal distribution.
Reference: Alexander (2008), Market Risk Analysis IV, Section IV.4.5.
"""

import scipy.stats as stats


def calculate_bayesian_posterior(
    mu_likelihood: float, sigma_likelihood: float, mu_prior: float, sigma_prior: float
) -> tuple:
    """
    Combines objective data (likelihood) with personal views (prior)
    to output Bayesian posterior expected return and volatility.
    """
    var_likelihood = sigma_likelihood**2
    var_prior = sigma_prior**2

    # Calculate Posterior Variance (Notice it will be lower than both components)
    posterior_var = 1.0 / ((1.0 / var_likelihood) + (1.0 / var_prior))
    posterior_sigma = posterior_var**0.5

    # Calculate Posterior Mean (A weighted average based on certainty)
    posterior_mu = (posterior_var / var_likelihood) * mu_likelihood + (
        posterior_var / var_prior
    ) * mu_prior

    return posterior_mu, posterior_sigma


def calculate_bayesian_var(posterior_mu: float, posterior_sigma: float, alpha: float) -> float:
    """Calculates the VaR using the new Bayesian posterior normal parameters."""
    z_score = stats.norm.ppf(1 - alpha)
    return (z_score * posterior_sigma) - posterior_mu


def compute(
    mu_likelihood: float,
    sigma_likelihood: float,
    mu_prior: float,
    sigma_prior: float,
    alpha: float = 0.01,
) -> dict:
    """Standard facade: Bayesian posterior VaR as a JSON-serializable dict.

    Parameters:
    mu_likelihood, sigma_likelihood (float): Moments of the data likelihood.
    mu_prior, sigma_prior (float): Prior moments (sigma > 0).
    alpha (float): Tail probability in (0, 1), e.g. 0.01.

    Returns:
    dict: {"method", "alpha", "posterior_mu", "posterior_sigma", "var"}.
    """
    if sigma_likelihood <= 0 or sigma_prior <= 0:
        raise ValueError("sigma_likelihood and sigma_prior must be positive")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in the open interval (0, 1)")

    post_mu, post_sigma = calculate_bayesian_posterior(
        float(mu_likelihood), float(sigma_likelihood), float(mu_prior), float(sigma_prior)
    )
    var = calculate_bayesian_var(post_mu, post_sigma, float(alpha))
    return {
        "method": "bayesian_posterior",
        "alpha": float(alpha),
        "posterior_mu": float(post_mu),
        "posterior_sigma": float(post_sigma),
        "var": float(var),
    }
