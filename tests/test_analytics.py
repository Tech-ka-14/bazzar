"""P7-C: service-layer tests for backend/analytics.py (roadmap 7.3).

Seeded DuckDB fixtures with synthetic deterministic close series (no
network). Known-answer spot checks compare the service output against
``quant.api`` computed directly on the same returns; the backtest test uses
a constructed series whose exceptions are known by construction.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pytest

from backend import analytics
from backend.db import get_connection, initialize_database
from quant import api as quant_api


def _returns_to_closes(returns: np.ndarray, start: float = 100.0) -> np.ndarray:
    return start * np.concatenate([[1.0], np.cumprod(1.0 + returns)])


def _seed_symbol(con, symbol: str, closes: np.ndarray) -> None:
    d0 = dt.date(2024, 1, 1)
    rows = [
        (symbol, "NSE", d0 + dt.timedelta(days=i), c, c, c, c, 1000) for i, c in enumerate(closes)
    ]
    con.executemany(
        "INSERT INTO daily_ohlcv (symbol, exchange, date, open, high, low, close, volume)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    initialize_database()
    con = get_connection()
    # Deterministic pseudo-random series (seeded, no network).
    rng = np.random.default_rng(20261012)
    _seed_symbol(con, "INFY", _returns_to_closes(rng.normal(0.0005, 0.012, 400)))
    _seed_symbol(con, "TCS", _returns_to_closes(rng.normal(0.0004, 0.010, 400), start=50.0))
    # Short series for the insufficient-data paths.
    _seed_symbol(con, "SHORT", _returns_to_closes(rng.normal(0.0, 0.01, 50)))
    yield con
    con.close()


def _service_returns(con, symbol: str) -> np.ndarray:
    """Recompute the service's returns straight from the seeded bars."""
    rows = con.execute(
        "SELECT close FROM daily_ohlcv WHERE symbol = ? AND exchange = 'NSE' ORDER BY date",
        (symbol,),
    ).fetchall()
    closes = np.array([r[0] for r in rows], dtype=float)
    return closes[1:] / closes[:-1] - 1.0


class TestVar:
    def test_known_answer_matches_quant_api(self, db):
        for method in ("historical", "parametric", "montecarlo"):
            payload = analytics.get_var(db, "INFY", method, 0.99)
            returns = _service_returns(db, "INFY")
            expected_var = quant_api.compute_var(returns, method, 0.99)["var"]
            expected_es = quant_api.compute_es(returns, method, 0.99)["es"]
            assert payload["var_pct"] == pytest.approx(expected_var, rel=1e-12)
            assert payload["es_pct"] == pytest.approx(expected_es, rel=1e-12)
            assert payload["n_obs"] == returns.size
            assert payload["cached"] is False

    def test_payload_metadata(self, db):
        payload = analytics.get_var(db, "INFY", "historical", 0.95)
        assert payload["symbol"] == "INFY"
        assert payload["method"] == "historical"
        assert payload["confidence"] == 0.95
        assert payload["var_value"] is None  # no position size — never fabricated
        assert payload["asOf"] == "2025-02-04"  # day 400 after 2024-01-01
        assert payload["source"] == "duckdb"

    def test_unknown_method_raises_keyerror(self, db):
        with pytest.raises(KeyError, match="available"):
            analytics.get_var(db, "INFY", "not-a-method")

    def test_unknown_symbol_raises(self, db):
        with pytest.raises(analytics.UnknownSymbolError):
            analytics.get_var(db, "NOPE")

    def test_insufficient_data_raises(self, db):
        with pytest.raises(analytics.InsufficientDataError, match="insufficient data"):
            analytics.get_var(db, "SHORT")

    def test_cache_hit_replays_payload(self, db):
        first = analytics.get_var(db, "INFY", "parametric", 0.99)
        second = analytics.get_var(db, "INFY", "parametric", 0.99)
        assert first["cached"] is False
        assert second["cached"] is True
        assert {k: v for k, v in second.items() if k != "cached"} == {
            k: v for k, v in first.items() if k != "cached"
        }

    def test_new_bar_invalidates_cache(self, db):
        assert analytics.get_var(db, "INFY", "historical", 0.99)["cached"] is False
        _seed_symbol(db, "INFY2", _returns_to_closes(np.full(300, 0.001)))
        # Same params but a different symbol is a different cache key...
        assert analytics.get_var(db, "INFY2", "historical", 0.99)["cached"] is False
        # ...and appending a bar changes the fingerprint for the same key.
        db.execute(
            "INSERT INTO daily_ohlcv VALUES ('INFY2', 'NSE', DATE '2025-01-01',"
            " 101, 101, 101, 101, 1000)"
        )
        assert analytics.get_var(db, "INFY2", "historical", 0.99)["cached"] is False
        assert analytics.get_var(db, "INFY2", "historical", 0.99)["cached"] is True


class TestVolatility:
    def test_ewma_matches_quant_api(self, db):
        payload = analytics.get_volatility(db, "INFY", "ewma")
        returns = _service_returns(db, "INFY")
        expected = quant_api.compute_volatility(
            returns, "ewma", lambda_param=0.94, annualization=252
        )
        assert payload["current_vol"] == pytest.approx(expected["current_volatility"], rel=1e-12)
        assert payload["annualized_vol"] == pytest.approx(
            expected["annualized_volatility"], rel=1e-12
        )
        assert payload["params"] == {"lambda": 0.94}

    def test_garch_params_shape(self, db):
        payload = analytics.get_volatility(db, "INFY", "garch")
        assert set(payload["params"]) == {"dist", "omega", "alpha", "beta", "persistence"}
        assert payload["annualized_vol"] == pytest.approx(
            payload["current_vol"] * np.sqrt(252), rel=1e-12
        )

    def test_unknown_model_raises(self, db):
        with pytest.raises(KeyError, match="available"):
            analytics.get_volatility(db, "INFY", "not-a-model")

    def test_vol_needs_fewer_obs_than_var(self, db):
        # 50 closes → 49 returns < 60: still insufficient for volatility.
        with pytest.raises(analytics.InsufficientDataError):
            analytics.get_volatility(db, "SHORT", "ewma")


class TestPortfolioRisk:
    def test_matches_quant_api(self, db):
        payload = analytics.get_portfolio_risk(db, {"INFY": 0.6, "TCS": 0.4}, 0.99)
        returns_infy = _service_returns(db, "INFY")
        returns_tcs = _service_returns(db, "TCS")
        matrix = np.column_stack([returns_infy, returns_tcs])
        expected = quant_api.compute_portfolio_risk(matrix, [0.6, 0.4], 0.99)
        assert payload["var_pct"] == pytest.approx(expected["diversified_var"], rel=1e-12)
        assert payload["n_obs"] == expected["n_obs"]
        assert set(payload["component_var"]) == {"INFY", "TCS"}
        assert sum(payload["component_var"].values()) == pytest.approx(payload["var_pct"], rel=1e-9)
        # Parametric portfolio ES is above VaR by construction.
        assert payload["es_pct"] > payload["var_pct"]

    def test_weights_must_sum_to_one(self, db):
        with pytest.raises(ValueError, match="sum to 1"):
            analytics.get_portfolio_risk(db, {"INFY": 0.6, "TCS": 0.2})

    def test_empty_weights_rejected(self, db):
        with pytest.raises(ValueError, match="at least one"):
            analytics.get_portfolio_risk(db, {})

    def test_unknown_leg_raises(self, db):
        with pytest.raises(analytics.UnknownSymbolError):
            analytics.get_portfolio_risk(db, {"INFY": 0.6, "NOPE": 0.4})

    def test_cache_hit(self, db):
        first = analytics.get_portfolio_risk(db, {"INFY": 0.6, "TCS": 0.4})
        second = analytics.get_portfolio_risk(db, {"TCS": 0.4, "INFY": 0.6})
        assert first["cached"] is False
        assert second["cached"] is True  # weight order does not matter
        assert second["weights"] == first["weights"]


class TestVarBacktest:
    @staticmethod
    def _constructed_closes() -> np.ndarray:
        """Estimation window with a stable -2% alpha-quantile, then 30
        one-day-ahead days of which exactly 3 crash below -VaR."""
        window = np.tile(np.array([-0.02, -0.01, 0.0, 0.01, 0.02]), 50)  # 250
        test_days = np.zeros(30)
        test_days[[5, 17, 29]] = -0.03  # 3 known exceptions
        return _returns_to_closes(np.concatenate([window, test_days]))

    def test_exceptions_known_by_construction(self, db):
        _seed_symbol(db, "BT", self._constructed_closes())
        payload = analytics.get_var_backtest(db, "BT", 0.95)
        assert payload["n_obs"] == 30
        assert payload["exceptions"] == 3
        assert payload["exception_rate"] == pytest.approx(3 / 30)
        assert payload["expected_exceptions"] == pytest.approx(30 * 0.05)
        assert payload["basel_zone"] in ("green", "amber", "red")
        assert payload["kupiec"]["decision"] in ("reject", "fail_to_reject")
        assert payload["christoffersen"] is not None
        assert payload["window"] == analytics.BACKTEST_WINDOW

    def test_too_short_for_backtest(self, db):
        # 400 returns is fine for VaR but the backtest needs window + 30.
        _seed_symbol(db, "MID", _returns_to_closes(np.full(260, 0.001)))
        with pytest.raises(analytics.InsufficientDataError):
            analytics.get_var_backtest(db, "MID", 0.95)

    def test_cache_hit(self, db):
        _seed_symbol(db, "BT", self._constructed_closes())
        first = analytics.get_var_backtest(db, "BT", 0.95)
        second = analytics.get_var_backtest(db, "BT", 0.95)
        assert first["cached"] is False
        assert second["cached"] is True
        assert second["exceptions"] == first["exceptions"] == 3
