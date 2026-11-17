"""GARCH(1,1) volatility models: likelihoods and MLE estimation.

Variance recursion: sigma^2_t = omega + alpha * r_{t-1}^2 + beta *
sigma^2_{t-1}, initialized at the unconditional sample variance. Innovations
are Student-t (``student_t_garch_loglik``) or normal (``normal_garch_loglik``).
Stationarity requires alpha + beta < 1; the unconditional (long-run)
variance is omega / (1 - alpha - beta). Reference: Bollerslev (1986);
Alexander (2008), Market Risk Analysis II, Section II.4.
"""

import numpy as np
import scipy.optimize as opt
import scipy.special as sp


def student_t_garch_loglik(params, returns):
    """
    Calculates the negative log-likelihood of a GARCH(1,1) model
    with Student-t distributed errors.
    params = [omega, alpha, beta, nu]
    """
    omega, alpha, beta, nu = params
    T = len(returns)

    # Enforce strict boundary constraints
    if omega <= 0 or alpha < 0 or beta < 0 or alpha + beta >= 1 or nu <= 2.01:
        return np.inf

    # Initialize variance array with sample variance
    sigma2 = np.zeros(T)
    sigma2[0] = np.var(returns)

    log_likelihood = 0.0

    # Pre-compute constant gamma terms for efficiency
    term1 = sp.gammaln((nu + 1) / 2) - sp.gammaln(nu / 2) - 0.5 * np.log(np.pi * (nu - 2))

    for t in range(1, T):
        # GARCH(1,1) variance recursion
        sigma2[t] = omega + alpha * (returns[t - 1] ** 2) + beta * sigma2[t - 1]

        # Student-t log-likelihood computation
        term2 = -0.5 * np.log(sigma2[t])
        term3 = -((nu + 1) / 2) * np.log(1 + (returns[t] ** 2) / ((nu - 2) * sigma2[t]))

        log_likelihood += term1 + term2 + term3

    # Return negative log-likelihood for the SciPy minimizer
    return -log_likelihood


def normal_garch_loglik(params, returns):
    """
    Calculates the negative log-likelihood of a GARCH(1,1) model
    with normally distributed errors.
    params = [omega, alpha, beta]
    """
    omega, alpha, beta = params
    T = len(returns)

    # Enforce strict boundary constraints
    if omega <= 0 or alpha < 0 or beta < 0 or alpha + beta >= 1:
        return np.inf

    # Initialize variance array with sample variance
    sigma2 = np.zeros(T)
    sigma2[0] = np.var(returns)

    log_likelihood = 0.0
    for t in range(1, T):
        # GARCH(1,1) variance recursion
        sigma2[t] = omega + alpha * (returns[t - 1] ** 2) + beta * sigma2[t - 1]

        # Gaussian log-likelihood contribution
        log_likelihood += (
            -0.5 * np.log(2.0 * np.pi)
            - 0.5 * np.log(sigma2[t])
            - 0.5 * (returns[t] ** 2) / sigma2[t]
        )

    # Return negative log-likelihood for the SciPy minimizer
    return -log_likelihood


def garch11_conditional_variance(returns, omega, alpha, beta):
    """
    Evaluates the GARCH(1,1) conditional variance path for given parameters,
    initialized at the unconditional sample variance (same convention as the
    likelihood functions in this module).
    """
    returns = np.asarray(returns, dtype=float).ravel()
    T = len(returns)
    sigma2 = np.zeros(T)
    sigma2[0] = np.var(returns)
    for t in range(1, T):
        sigma2[t] = omega + alpha * (returns[t - 1] ** 2) + beta * sigma2[t - 1]
    return sigma2


def estimate_garch11(returns, dist: str = "normal") -> dict:
    """
    Fits a GARCH(1,1) model to a return series by maximum likelihood.

    Parameters:
    returns: 1-D array-like of returns (fractions).
    dist (str): Innovation distribution, "normal" or "student_t".

    Returns:
    dict: parameter estimates, persistence, long-run volatility, the final
    conditional variance, the maximized log-likelihood and a convergence
    flag. All values are plain floats (JSON-serializable).
    """
    returns = np.asarray(returns, dtype=float).ravel()
    if returns.size < 50:
        raise ValueError("GARCH(1,1) estimation requires at least 50 observations")

    var0 = float(np.var(returns))
    if var0 <= 0.0:
        raise ValueError("returns have zero variance; GARCH is not identified")

    # Fit on variance-standardized returns so that omega is O(0.1) like
    # alpha/beta/nu; this keeps the numerical gradients of L-BFGS-B well
    # conditioned. omega is scaled back by var0 afterwards (alpha, beta, nu
    # are scale-invariant), and the likelihood is re-evaluated on the
    # original scale for reporting.
    scale = float(np.sqrt(var0))
    scaled_returns = returns / scale

    if dist == "normal":
        loglik = normal_garch_loglik
        x0 = np.array([0.1, 0.1, 0.8])
        bounds = [(1e-12, None), (1e-8, 1.0 - 1e-8), (1e-8, 1.0 - 1e-8)]
    elif dist == "student_t":
        loglik = student_t_garch_loglik
        x0 = np.array([0.1, 0.1, 0.8, 8.0])
        bounds = [(1e-12, None), (1e-8, 1.0 - 1e-8), (1e-8, 1.0 - 1e-8), (2.01, 200.0)]
    else:
        raise ValueError("dist must be 'normal' or 'student_t'")

    def objective(params):
        # L-BFGS-B's numerical differentiation breaks on np.inf values, so
        # infeasible regions are mapped to a large finite penalty instead.
        value = loglik(params, scaled_returns)
        return value if np.isfinite(value) else 1e12

    result = opt.minimize(objective, x0, method="L-BFGS-B", bounds=bounds)

    omega = float(result.x[0]) * var0
    alpha = float(result.x[1])
    beta = float(result.x[2])
    sigma2 = garch11_conditional_variance(returns, omega, alpha, beta)

    # Re-evaluate the maximized likelihood on the original return scale.
    if dist == "normal":
        max_loglik = -normal_garch_loglik([omega, alpha, beta], returns)
    else:
        max_loglik = -student_t_garch_loglik([omega, alpha, beta, float(result.x[3])], returns)

    output = {
        "dist": dist,
        "omega": omega,
        "alpha": alpha,
        "beta": beta,
        "persistence": alpha + beta,
        "long_run_variance": omega / max(1.0 - alpha - beta, 1e-12),
        "current_variance": float(sigma2[-1]),
        "log_likelihood": float(max_loglik),
        "converged": bool(result.success),
        "n": int(returns.size),
    }
    output["long_run_volatility"] = float(np.sqrt(output["long_run_variance"]))
    output["current_volatility"] = float(np.sqrt(output["current_variance"]))
    if dist == "student_t":
        output["nu"] = float(result.x[3])
    return output


def compute(returns, dist: str = "normal") -> dict:
    """Standard facade: GARCH(1,1) MLE fit as a JSON-serializable dict.

    Parameters:
    returns: 1-D array-like of returns (fractions).
    dist (str): Innovation distribution, "normal" or "student_t".

    Returns:
    dict: {"model", "dist", "omega", "alpha", "beta", "nu" (student_t only),
    "persistence", "long_run_volatility", "current_volatility", ...}.
    """
    estimates = estimate_garch11(returns, dist=dist)
    return {"model": "garch", **estimates}


# Example implementation
# initial_guess = [0.00001, 0.1, 0.8, 5.0] # omega, alpha, beta, nu
# bounds = ((1e-6, None), (0.001, 0.99), (0.001, 0.99), (2.01, 100))
# result = minimize(student_t_garch_loglik, initial_guess, args=(returns,), bounds=bounds)
