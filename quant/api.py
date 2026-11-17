"""Thin dispatch layer over the standardized flagship quant modules.

This is the ONLY surface the backend analytics layer (P7-B) should use for
the roadmap-7.3 endpoints. Each function delegates to a standardized module
(see quant/README.md for the standard), returns plain JSON-serializable
dicts, and raises KeyError listing the available options on an unknown
method/model name.
"""

import numpy as np
from scipy.stats import norm

from quant.copulas import copula_monte_carlo_var
from quant.risk import (
    basel_regulatory_backtest,
    conditional_var_metrics,
    correlated_monte_carlo,
    delvar_gradient_marginal,
    historical_simulation_var,
    normal_linear_var,
    var_coverage_tests,
)
from quant.timeseries import ewma_variance_volatility, student_t_garch

VAR_METHODS = ("historical", "parametric", "montecarlo")
ES_METHODS = ("historical", "parametric", "montecarlo")
VOLATILITY_MODELS = ("ewma", "garch")


def _as_returns(returns) -> np.ndarray:
    """Coerces input to a 1-D float array with basic validation."""
    array = np.asarray(returns, dtype=float).ravel()
    if array.size < 2:
        raise ValueError("returns must contain at least two observations")
    return array


def _check_choice(name: str, value: str, available) -> str:
    """Validates a method/model name, raising KeyError with the options."""
    value = str(value).lower()
    if value not in available:
        raise KeyError(f"unknown {name} {value!r}; available: {sorted(available)}")
    return value


def _check_confidence(confidence: float) -> float:
    confidence = float(confidence)
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in the open interval (0, 1)")
    return confidence


def _simulate_single_asset(returns: np.ndarray, num_simulations: int, seed: int) -> np.ndarray:
    """Simulates normal scenarios matching the sample moments of returns."""
    mu = float(np.mean(returns))
    sigma = float(np.std(returns, ddof=1))
    if seed is not None:
        # The simulation engine uses the legacy global numpy RNG.
        np.random.seed(int(seed))
    simulated = correlated_monte_carlo.simulate_correlated_normals(
        np.array([mu]), np.array([[sigma**2]]), int(num_simulations)
    )
    return simulated.ravel()


def compute_var(
    returns,
    method: str = "historical",
    confidence: float = 0.99,
    num_simulations: int = 10_000,
    seed: int = 42,
) -> dict:
    """Value at Risk of a return series under the requested method.

    method: "historical" (empirical quantile, linear interpolation),
    "parametric" (normal variance-covariance with fitted mu/sigma) or
    "montecarlo" (seeded normal simulation with fitted mu/sigma).

    Returns a JSON-serializable dict with at least {"method", "confidence",
    "var"} where "var" is the positive loss fraction.
    """
    method = _check_choice("VaR method", method, VAR_METHODS)
    confidence = _check_confidence(confidence)
    returns = _as_returns(returns)

    if method == "historical":
        return historical_simulation_var.compute(returns, confidence=confidence)
    if method == "parametric":
        return normal_linear_var.compute(returns, confidence=confidence)

    # method == "montecarlo"
    simulated = _simulate_single_asset(returns, num_simulations, seed)
    result = copula_monte_carlo_var.compute(simulated, confidence=confidence)
    result["seed"] = int(seed)
    return result


def compute_es(
    returns,
    method: str = "historical",
    confidence: float = 0.99,
    num_simulations: int = 10_000,
    seed: int = 42,
) -> dict:
    """Expected shortfall (ETL) of a return series under the requested method.

    method: "historical" (average loss beyond the "lower"-quantile VaR
    threshold), "parametric" (normal ES: sigma * phi(z)/alpha - mu) or
    "montecarlo" (seeded normal simulation, tail average).

    Returns a JSON-serializable dict with at least {"method", "confidence",
    "es"} where "es" is the positive expected loss fraction in the tail.
    """
    method = _check_choice("ES method", method, ES_METHODS)
    confidence = _check_confidence(confidence)
    returns = _as_returns(returns)

    if method == "historical":
        result = conditional_var_metrics.compute(returns, confidence=confidence)
        return {
            "method": "historical",
            "confidence": confidence,
            "n": result["n"],
            "var": result["var"],
            "es": result["es"],
        }
    if method == "parametric":
        mu = float(np.mean(returns))
        sigma = float(np.std(returns, ddof=1))
        alpha = 1.0 - confidence
        z = float(norm.ppf(1.0 - alpha))
        var = z * sigma - mu
        es = sigma * float(norm.pdf(z)) / alpha - mu
        return {
            "method": "parametric",
            "confidence": confidence,
            "n": int(returns.size),
            "mu": mu,
            "sigma": sigma,
            "var": float(var),
            "es": float(es),
        }

    # method == "montecarlo"
    simulated = _simulate_single_asset(returns, num_simulations, seed)
    alpha = 1.0 - confidence
    var_percentile = float(np.quantile(simulated, alpha, method="linear"))
    tail = simulated[simulated <= var_percentile]
    return {
        "method": "montecarlo",
        "confidence": confidence,
        "n_simulations": int(simulated.size),
        "seed": int(seed),
        "var": float(-var_percentile),
        "es": float(-np.mean(tail)),
    }


def compute_volatility(returns, model: str = "ewma", **params) -> dict:
    """Current conditional volatility of a return series.

    model: "ewma" (RiskMetrics recursion; params: lambda_param,
    annualization) or "garch" (GARCH(1,1) MLE; params: dist = "normal" or
    "student_t"). Returns a JSON-serializable dict with at least {"model",
    "current_volatility"}.
    """
    model = _check_choice("volatility model", model, VOLATILITY_MODELS)
    returns = _as_returns(returns)

    if model == "ewma":
        lambda_param = float(params.get("lambda_param", 0.94))
        annualization = int(params.get("annualization", 1))
        return ewma_variance_volatility.compute(
            returns, lambda_param=lambda_param, annualization=annualization
        )

    # model == "garch"
    dist = str(params.get("dist", "normal")).lower()
    if dist not in ("normal", "student_t"):
        raise KeyError(f"unknown GARCH dist {dist!r}; available: ['normal', 'student_t']")
    return student_t_garch.compute(returns, dist=dist)


def compute_portfolio_risk(returns_df, weights, confidence: float = 0.99) -> dict:
    """Normal linear portfolio risk with Euler (component VaR) decomposition.

    Parameters:
    returns_df: T x K array-like or pandas DataFrame of asset returns.
    weights: 1-D array-like of portfolio weights (fractions of portfolio
    value), one per asset.
    confidence (float): VaR confidence level in (0, 1).

    Returns a JSON-serializable dict: {"confidence", "n_obs", "assets",
    "portfolio_volatility", "diversified_var", "undiversified_var",
    "component_var", "component_share"} where diversified_var is the
    positive loss fraction z * sqrt(w' Sigma w) and the component VaRs
    (DelVaR Euler decomposition) sum to it.
    """
    confidence = _check_confidence(confidence)
    assets = list(getattr(returns_df, "columns", []))
    matrix = np.asarray(returns_df, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] < 2 or matrix.shape[1] < 1:
        raise ValueError("returns_df must be a T x K array with T >= 2")
    if not assets:
        assets = [f"asset_{i}" for i in range(matrix.shape[1])]

    weights = np.asarray(weights, dtype=float).ravel()
    if weights.size != matrix.shape[1]:
        raise ValueError("weights must have one entry per asset (column)")

    alpha = 1.0 - confidence
    z = float(norm.ppf(1.0 - alpha))
    cov = np.cov(matrix, rowvar=False, ddof=1)
    cov = np.atleast_2d(cov)

    portfolio_variance = float(weights @ cov @ weights)
    portfolio_volatility = float(np.sqrt(portfolio_variance))
    diversified_var = z * portfolio_volatility

    asset_vols = np.sqrt(np.diag(cov))
    undiversified_var = float(z * np.sum(np.abs(weights) * asset_vols))

    decomposition = delvar_gradient_marginal.compute(weights, cov, confidence=confidence)
    component_var = decomposition["component_var"]
    component_share = [
        (c / diversified_var) if diversified_var > 0.0 else 0.0 for c in component_var
    ]

    return {
        "confidence": confidence,
        "n_obs": int(matrix.shape[0]),
        "assets": [str(a) for a in assets],
        "portfolio_volatility": portfolio_volatility,
        "diversified_var": float(diversified_var),
        "undiversified_var": undiversified_var,
        "component_var": component_var,
        "component_share": component_share,
    }


def compute_var_backtest(exceptions, n: int, confidence: float = 0.99) -> dict:
    """Backtest a VaR model from its exceedances.

    Parameters:
    exceptions: either the count of exceedances (int) or a 0/1 array-like of
    exceedance indicators (length n); in the latter case the Christoffersen
    independence test is included.
    n (int): Number of backtest observations (e.g. 250).
    confidence (float): The VaR confidence level that was used, in (0, 1).

    Returns a JSON-serializable dict: {"n", "n_exceedances", "confidence",
    "expected_exceedances", "kupiec": {...}, "christoffersen": {...}?,
    "basel": {...}}.
    """
    confidence = _check_confidence(confidence)
    n = int(n)
    if n < 1:
        raise ValueError("n must be a positive integer")

    transitions = None
    if np.isscalar(exceptions):
        n_exceedances = int(exceptions)
    else:
        indicators = np.asarray(exceptions, dtype=int).ravel()
        if indicators.size != n:
            raise ValueError("exceptions indicator array must have length n")
        if not np.all((indicators == 0) | (indicators == 1)):
            raise ValueError("exceptions indicators must be 0 or 1")
        n_exceedances = int(np.sum(indicators))
        transitions = {
            "n00": int(np.sum((indicators[:-1] == 0) & (indicators[1:] == 0))),
            "n01": int(np.sum((indicators[:-1] == 0) & (indicators[1:] == 1))),
            "n10": int(np.sum((indicators[:-1] == 1) & (indicators[1:] == 0))),
            "n11": int(np.sum((indicators[:-1] == 1) & (indicators[1:] == 1))),
        }

    coverage = var_coverage_tests.compute(
        n_obs=n, n_exceedances=n_exceedances, confidence=confidence, transitions=transitions
    )
    result = {
        "n": n,
        "n_exceedances": n_exceedances,
        "confidence": confidence,
        "expected_exceedances": float(n * (1.0 - confidence)),
        "kupiec": {"stat": coverage["kupiec_stat"], "p_value": coverage["kupiec_p"]},
        "basel": basel_regulatory_backtest.compute(n_exceedances),
    }
    if transitions is not None:
        result["christoffersen"] = {
            "stat": coverage["christoffersen_stat"],
            "p_value": coverage["christoffersen_p"],
            "transitions": transitions,
        }
        result["conditional_coverage"] = {
            "stat": coverage["conditional_coverage_stat"],
            "p_value": coverage["conditional_coverage_p"],
        }
    return result
