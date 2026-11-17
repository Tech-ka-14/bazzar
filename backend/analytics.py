"""P7-C analytics service layer (roadmap 7.3).

Computes Value-at-Risk, expected shortfall, volatility, portfolio risk and
VaR backtests from the daily close history stored in DuckDB
(``daily_ohlcv``), exclusively through the ``quant.api`` dispatch layer —
this module must never import the individual ``quant`` modules directly
(see ``quant/README.md`` "The dispatch layer").

Design choices (documented per the SPEC "never fabricate" rule):

* **Returns convention** — simple daily returns
  ``r_t = close_t / close_{t-1} - 1`` (fractions, e.g. -0.02), matching the
  flagship-module convention (``quant/risk/historical_simulation_var.py``
  takes "returns (fractions)"). VaR/ES are reported as *positive* loss
  fractions.
* **Minimum observations** — hard floors below which we refuse to answer
  with a clean ``insufficient_data`` error instead of fabricating a number:

  * VaR/ES and portfolio risk: 250 return observations (~1 trading year),
    the canonical historical-simulation window.
  * Volatility (EWMA and GARCH): 60 observations (~3 months), the minimum
    for a halfway stable GARCH(1,1) MLE.
  * VaR backtest: a 250-day estimation window plus at least 30 one-day-ahead
    backtest days, i.e. 280 returns in total.
* **Backtest approach** — rolling one-day-ahead *historical simulation*
  VaR: for each day ``t`` after the estimation window, VaR is the empirical
  alpha-quantile (linear interpolation, the exact flagship semantics) of the
  trailing 250 returns; an exception is a realized return below ``-VaR``.
  The 0/1 indicator series feeds ``quant.api.compute_var_backtest``, which
  adds the Christoffersen independence test on top of Kupiec + Basel zone.
* **Caching** — the DuckDB ``analytics_cache`` table (migration 0005). The
  key is ``sha256(endpoint | canonical-params-json | data-fingerprint)`` and
  the fingerprint is ``MAX(date):row-count`` of the underlying close series
  (per symbol for portfolios), so a fresh ingest invalidates automatically.
  A hit replays the stored payload with ``cached: true``.

Every payload carries ``asOf`` (latest underlying bar date) and
``source: "duckdb"`` — the numbers are computed from the local DuckDB store
regardless of which upstream provider synced the bars.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

import numpy as np
from scipy.stats import norm

from quant import api as quant_api

# Minimum return observations per computation class (see module docstring).
MIN_VAR_OBS = 250
MIN_VOL_OBS = 60
MIN_PORTFOLIO_OBS = 250
BACKTEST_WINDOW = 250
MIN_BACKTEST_DAYS = 30
MIN_BACKTEST_OBS = BACKTEST_WINDOW + MIN_BACKTEST_DAYS

# Tolerance on the portfolio weights summing to 1 (fractions, not percent).
WEIGHT_SUM_TOLERANCE = 1e-4

# Annualization factor for daily → annual volatility / ratios (trading days).
TRADING_DAYS_PER_YEAR = 252

# Significance level for the backtest coverage-test decisions.
BACKTEST_ALPHA = 0.05

DATA_SOURCE = "duckdb"


class UnknownSymbolError(Exception):
    """The symbol has no rows at all in daily_ohlcv (→ HTTP 404)."""


class InsufficientDataError(Exception):
    """Too little history to compute a non-fabricated number (→ HTTP 422)."""


# --- data access -------------------------------------------------------------


def _fetch_close_series(con: Any, symbol: str) -> tuple[str, list[tuple[Any, float]]]:
    """Daily (date, close) bars for a symbol, oldest first.

    Picks the NSE exchange when the symbol trades on several, else the
    exchange with the most history. Raises UnknownSymbolError when the
    symbol has never been synced.
    """
    symbol = symbol.strip().upper()
    rows = con.execute(
        "SELECT exchange, COUNT(*) FROM daily_ohlcv WHERE symbol = ? GROUP BY exchange",
        (symbol,),
    ).fetchall()
    if not rows:
        raise UnknownSymbolError(f"unknown symbol {symbol!r}: no daily bars synced")
    counts = {str(r[0]): int(r[1]) for r in rows}
    exchange = "NSE" if "NSE" in counts else max(counts, key=lambda k: counts[k])
    bars = con.execute(
        "SELECT date, close FROM daily_ohlcv"
        " WHERE symbol = ? AND exchange = ? AND close > 0 ORDER BY date",
        (symbol, exchange),
    ).fetchall()
    return symbol, [(r[0], float(r[1])) for r in bars]


def _simple_returns(bars: list[tuple[Any, float]]) -> np.ndarray:
    """Simple close-to-close returns r_t = close_t/close_{t-1} - 1."""
    closes = np.array([close for _, close in bars], dtype=float)
    if closes.size < 2:
        return np.array([], dtype=float)
    return closes[1:] / closes[:-1] - 1.0


def _asof(bars: list[tuple[Any, float]]) -> str:
    return str(bars[-1][0])[:10]


def _fingerprint(bars: list[tuple[Any, float]]) -> str:
    """Cache-invalidation fingerprint: latest bar date + row count."""
    return f"{_asof(bars)}:{len(bars)}"


def _require_obs(n_obs: int, minimum: int, what: str) -> None:
    if n_obs < minimum:
        raise InsufficientDataError(
            f"insufficient data for {what}: {n_obs} return observations "
            f"available, at least {minimum} required"
        )


# --- cache -------------------------------------------------------------------


def _cache_key(endpoint: str, params: dict[str, Any], fingerprint: str) -> str:
    canonical = json.dumps(params, sort_keys=True)
    return hashlib.sha256(f"{endpoint}|{canonical}|{fingerprint}".encode()).hexdigest()


def _cached(
    con: Any,
    endpoint: str,
    params: dict[str, Any],
    fingerprint: str,
    compute: Any,
) -> dict[str, Any]:
    """Return the cached payload for this key, or compute + store it."""
    key = _cache_key(endpoint, params, fingerprint)
    row = con.execute(
        "SELECT payload_json FROM analytics_cache WHERE cache_key = ?", (key,)
    ).fetchone()
    if row is not None:
        payload = json.loads(row[0])
        payload["cached"] = True
        return payload
    payload = compute()
    payload["cached"] = False
    con.execute(
        "INSERT OR REPLACE INTO analytics_cache"
        " (cache_key, endpoint, params_json, data_asof, payload_json, created_at)"
        " VALUES (?, ?, ?, ?, ?, now())",
        (key, endpoint, json.dumps(params, sort_keys=True), fingerprint, json.dumps(payload)),
    )
    return payload


# --- validation helpers -------------------------------------------------------


def _check_choice(name: str, value: str, available: tuple[str, ...]) -> str:
    value = str(value).strip().lower()
    if value not in available:
        raise KeyError(f"unknown {name} {value!r}; available: {sorted(available)}")
    return value


def _check_confidence(confidence: float) -> float:
    confidence = float(confidence)
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in the open interval (0, 1)")
    return confidence


# --- service functions ---------------------------------------------------------


def get_var(con: Any, symbol: str, method: str = "historical", confidence: float = 0.99) -> dict:
    """VaR + ES for one symbol's simple daily returns (positive loss fractions)."""
    method = _check_choice("VaR method", method, quant_api.VAR_METHODS)
    confidence = _check_confidence(confidence)
    symbol, bars = _fetch_close_series(con, symbol)
    returns = _simple_returns(bars)
    _require_obs(returns.size, MIN_VAR_OBS, f"VaR on {symbol}")

    params: dict[str, Any] = {"symbol": symbol, "method": method, "confidence": confidence}

    def compute() -> dict[str, Any]:
        var_result = quant_api.compute_var(returns, method, confidence)
        es_result = quant_api.compute_es(returns, method, confidence)
        return {
            "symbol": symbol,
            "method": method,
            "confidence": confidence,
            "var_pct": float(var_result["var"]),
            # Monetary VaR needs a position size, which the data layer does
            # not track — null, never fabricated (SPEC hard rule).
            "var_value": None,
            "es_pct": float(es_result["es"]),
            "n_obs": int(returns.size),
            "asOf": _asof(bars),
            "source": DATA_SOURCE,
        }

    return _cached(con, "var", params, _fingerprint(bars), compute)


def get_volatility(con: Any, symbol: str, model: str = "ewma") -> dict:
    """Current conditional daily volatility (+ annualized) for one symbol."""
    model = _check_choice("volatility model", model, quant_api.VOLATILITY_MODELS)
    symbol, bars = _fetch_close_series(con, symbol)
    returns = _simple_returns(bars)
    _require_obs(returns.size, MIN_VOL_OBS, f"volatility on {symbol}")

    params: dict[str, Any] = {"symbol": symbol, "model": model}

    def compute() -> dict[str, Any]:
        if model == "ewma":
            result = quant_api.compute_volatility(
                returns, "ewma", lambda_param=0.94, annualization=TRADING_DAYS_PER_YEAR
            )
            current = float(result["current_volatility"])
            annualized = float(result["annualized_volatility"])
            model_params: dict[str, Any] = {"lambda": float(result["lambda"])}
        else:  # garch
            result = quant_api.compute_volatility(returns, "garch")
            current = float(result["current_volatility"])
            annualized = current * math.sqrt(TRADING_DAYS_PER_YEAR)
            model_params = {
                "dist": result["dist"],
                "omega": float(result["omega"]),
                "alpha": float(result["alpha"]),
                "beta": float(result["beta"]),
                "persistence": float(result["persistence"]),
            }
        return {
            "symbol": symbol,
            "model": model,
            "current_vol": current,
            "annualized_vol": annualized,
            "params": model_params,
            "n_obs": int(returns.size),
            "asOf": _asof(bars),
            "source": DATA_SOURCE,
        }

    return _cached(con, "volatility", params, _fingerprint(bars), compute)


def get_portfolio_risk(con: Any, weights: dict[str, float], confidence: float = 0.99) -> dict:
    """Normal linear portfolio VaR/ES with the Euler component-VaR split.

    The legs are aligned on their common trading dates; ``asOf`` is the
    latest date common to every leg (the min of the per-leg last dates).
    Sharpe/Sortino are annualized from the daily portfolio returns with a
    zero risk-free rate (documented; no fabricated rate assumption).
    """
    confidence = _check_confidence(confidence)
    if not weights:
        raise ValueError("weights must name at least one symbol")
    clean: dict[str, float] = {}
    for raw_symbol, raw_weight in weights.items():
        weight = float(raw_weight)
        if not math.isfinite(weight):
            raise ValueError(f"weight for {raw_symbol!r} must be finite")
        clean[raw_symbol.strip().upper()] = weight
    total = sum(clean.values())
    if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
        raise ValueError(f"weights must sum to 1 (got {total:.6f})")

    series: dict[str, dict[Any, float]] = {}
    fingerprints: list[str] = []
    for symbol in sorted(clean):
        _, bars = _fetch_close_series(con, symbol)
        series[symbol] = dict(bars)
        fingerprints.append(f"{symbol}:{_fingerprint(bars)}")

    common_dates = sorted(set.intersection(*(set(d) for d in series.values())))
    symbols = sorted(clean)
    if len(common_dates) >= 2:
        closes = np.array([[series[s][d] for s in symbols] for d in common_dates], dtype=float)
        matrix = closes[1:] / closes[:-1] - 1.0
    else:
        matrix = np.empty((0, len(symbols)))
    _require_obs(matrix.shape[0], MIN_PORTFOLIO_OBS, "portfolio risk")

    w = np.array([clean[s] for s in symbols], dtype=float)
    params: dict[str, Any] = {
        "weights": {s: clean[s] for s in symbols},
        "confidence": confidence,
    }

    def compute() -> dict[str, Any]:
        risk = quant_api.compute_portfolio_risk(matrix, w, confidence)
        port_returns = matrix @ w
        mu = float(np.mean(port_returns))
        sigma = float(np.std(port_returns, ddof=1))
        alpha = 1.0 - confidence
        z = float(norm.ppf(1.0 - alpha))
        es = sigma * float(norm.pdf(z)) / alpha - mu
        annualizer = math.sqrt(TRADING_DAYS_PER_YEAR)
        sharpe = (mu / sigma * annualizer) if sigma > 0.0 else None
        downside = float(np.sqrt(np.mean(np.minimum(port_returns, 0.0) ** 2)))
        sortino = (mu / downside * annualizer) if downside > 0.0 else None
        return {
            "symbols": symbols,
            "weights": {s: clean[s] for s in symbols},
            "confidence": confidence,
            "var_pct": float(risk["diversified_var"]),
            "es_pct": float(es),
            "portfolio_volatility": float(risk["portfolio_volatility"]),
            "undiversified_var": float(risk["undiversified_var"]),
            "component_var": {
                s: float(v) for s, v in zip(symbols, risk["component_var"], strict=True)
            },
            "sharpe": sharpe,
            "sortino": sortino,
            "n_obs": int(matrix.shape[0]),
            "asOf": str(common_dates[-1])[:10],
            "source": DATA_SOURCE,
        }

    return _cached(con, "portfolio_risk", params, "|".join(fingerprints), compute)


def get_var_backtest(con: Any, symbol: str, confidence: float = 0.99) -> dict:
    """Rolling one-day-ahead historical-simulation VaR backtest.

    Exceptions are the days (after the 250-day estimation window) where the
    realized return fell below -VaR. Kupiec/Christoffersen decisions are at
    the 5% significance level; the Basel zone comes from the flagship
    traffic-light module.
    """
    confidence = _check_confidence(confidence)
    symbol, bars = _fetch_close_series(con, symbol)
    returns = _simple_returns(bars)
    _require_obs(returns.size, MIN_BACKTEST_OBS, f"VaR backtest on {symbol}")

    params: dict[str, Any] = {"symbol": symbol, "confidence": confidence}

    def compute() -> dict[str, Any]:
        indicators: list[int] = []
        for t in range(BACKTEST_WINDOW, returns.size):
            window = returns[t - BACKTEST_WINDOW : t]
            var_t = float(quant_api.compute_var(window, "historical", confidence)["var"])
            indicators.append(1 if float(returns[t]) < -var_t else 0)
        n = len(indicators)
        result = quant_api.compute_var_backtest(indicators, n, confidence)
        kupiec_p = float(result["kupiec"]["p_value"])
        christoffersen = result.get("christoffersen")
        return {
            "symbol": symbol,
            "method": "historical",
            "confidence": confidence,
            "window": BACKTEST_WINDOW,
            "n_obs": n,
            "exceptions": int(result["n_exceedances"]),
            "exception_rate": float(result["n_exceedances"]) / n,
            "expected_exceptions": float(result["expected_exceedances"]),
            "kupiec": {
                "lr": float(result["kupiec"]["stat"]),
                "p_value": kupiec_p,
                "decision": "reject" if kupiec_p < BACKTEST_ALPHA else "fail_to_reject",
            },
            "christoffersen": (
                {
                    "lr": float(christoffersen["stat"]),
                    "p_value": float(christoffersen["p_value"]),
                    "decision": (
                        "reject"
                        if float(christoffersen["p_value"]) < BACKTEST_ALPHA
                        else "fail_to_reject"
                    ),
                }
                if christoffersen is not None
                else None
            ),
            # The flagship Basel module uses the canonical Green/Yellow/Red
            # names; the API contract calls the middle zone "amber".
            "basel_zone": str(result["basel"]["zone"]).lower().replace("yellow", "amber"),
            "asOf": _asof(bars),
            "source": DATA_SOURCE,
        }

    return _cached(con, "var_backtest", params, _fingerprint(bars), compute)
