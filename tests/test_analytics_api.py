"""P7-C: API contract tests for the /api/v1/analytics/* endpoints.

Same conventions as tests/test_api_contracts.py: TestClient against a
throwaway BAZZAR_DATA_DIR with seeded deterministic price series, exact
response-shape keys, envelope checks on every failure path, and the cache
hit on the second identical call.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.db import get_connection
from backend.settings import get_settings


def _seed(con, symbol: str, n_returns: int, seed: int) -> None:
    rng = np.random.default_rng(seed)
    closes = 100.0 * np.concatenate([[1.0], np.cumprod(1.0 + rng.normal(0.0005, 0.012, n_returns))])
    d0 = dt.date(2024, 1, 1)
    con.executemany(
        "INSERT INTO daily_ohlcv (symbol, exchange, date, open, high, low, close, volume)"
        " VALUES (?, 'NSE', ?, ?, ?, ?, ?, 1000)",
        [(symbol, d0 + dt.timedelta(days=i), c, c, c, c) for i, c in enumerate(closes)],
    )


@pytest.fixture()
def api(tmp_path, monkeypatch):
    with monkeypatch.context() as m:
        m.setenv("BAZZAR_DATA_DIR", str(tmp_path))
        m.delenv("BAZZAR_API_TOKEN", raising=False)
        get_settings.cache_clear()
        from backend.server import app

        with TestClient(app) as client:
            with get_connection() as con:
                _seed(con, "INFY", 400, seed=11)
                _seed(con, "TCS", 400, seed=22)
                _seed(con, "SHORT", 50, seed=33)
            yield client
    get_settings.cache_clear()


def _assert_envelope(body, code):
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == code
    assert isinstance(body["error"]["message"], str) and body["error"]["message"]


VAR_KEYS = {
    "symbol",
    "method",
    "confidence",
    "var_pct",
    "var_value",
    "es_pct",
    "n_obs",
    "asOf",
    "source",
    "cached",
}


class TestVarEndpoint:
    def test_shape_and_cache(self, api):
        res = api.get("/api/v1/analytics/var", params={"symbol": "INFY"})
        assert res.status_code == 200
        body = res.json()
        assert set(body) == VAR_KEYS
        assert body["symbol"] == "INFY"
        assert body["method"] == "historical"
        assert body["cached"] is False
        assert body["var_pct"] > 0
        assert body["es_pct"] >= body["var_pct"]
        assert body["source"] == "duckdb"
        assert "x-request-id" in {k.lower() for k in res.headers}

        second = api.get("/api/v1/analytics/var", params={"symbol": "INFY"})
        assert second.status_code == 200
        body2 = second.json()
        assert body2["cached"] is True
        assert {k: v for k, v in body2.items() if k != "cached"} == {
            k: v for k, v in body.items() if k != "cached"
        }

    def test_all_methods(self, api):
        for method in ("historical", "parametric", "montecarlo"):
            res = api.get(
                "/api/v1/analytics/var",
                params={"symbol": "INFY", "method": method, "confidence": 0.95},
            )
            assert res.status_code == 200, method
            assert res.json()["method"] == method

    def test_deprecated_alias_mount(self, api):
        res = api.get("/api/analytics/var", params={"symbol": "INFY"})
        assert res.status_code == 200
        assert set(res.json()) == VAR_KEYS

    def test_unknown_method_400(self, api):
        res = api.get("/api/v1/analytics/var", params={"symbol": "INFY", "method": "nope"})
        assert res.status_code == 400
        body = res.json()
        _assert_envelope(body, "bad_request")
        assert "historical" in body["error"]["message"]
        assert "parametric" in body["error"]["message"]
        assert "montecarlo" in body["error"]["message"]

    def test_bad_confidence_400(self, api):
        res = api.get("/api/v1/analytics/var", params={"symbol": "INFY", "confidence": 1.5})
        assert res.status_code == 400
        _assert_envelope(res.json(), "bad_request")

    def test_unknown_symbol_404(self, api):
        res = api.get("/api/v1/analytics/var", params={"symbol": "NOPE"})
        assert res.status_code == 404
        _assert_envelope(res.json(), "not_found")

    def test_insufficient_data_422(self, api):
        res = api.get("/api/v1/analytics/var", params={"symbol": "SHORT"})
        assert res.status_code == 422
        _assert_envelope(res.json(), "insufficient_data")


class TestVolatilityEndpoint:
    KEYS = {
        "symbol",
        "model",
        "current_vol",
        "annualized_vol",
        "params",
        "n_obs",
        "asOf",
        "source",
        "cached",
    }

    def test_ewma_shape_and_cache(self, api):
        res = api.get("/api/v1/analytics/volatility", params={"symbol": "INFY", "model": "ewma"})
        assert res.status_code == 200
        body = res.json()
        assert set(body) == self.KEYS
        assert body["cached"] is False
        assert body["current_vol"] > 0
        assert body["annualized_vol"] > body["current_vol"]
        second = api.get("/api/v1/analytics/volatility", params={"symbol": "INFY", "model": "ewma"})
        assert second.json()["cached"] is True

    def test_garch_shape(self, api):
        res = api.get("/api/v1/analytics/volatility", params={"symbol": "INFY", "model": "garch"})
        assert res.status_code == 200
        body = res.json()
        assert set(body) == self.KEYS
        assert set(body["params"]) >= {"omega", "alpha", "beta"}

    def test_unknown_model_400(self, api):
        res = api.get("/api/v1/analytics/volatility", params={"symbol": "INFY", "model": "nope"})
        assert res.status_code == 400
        body = res.json()
        _assert_envelope(body, "bad_request")
        assert "ewma" in body["error"]["message"]
        assert "garch" in body["error"]["message"]

    def test_insufficient_data_422(self, api):
        res = api.get("/api/v1/analytics/volatility", params={"symbol": "SHORT"})
        assert res.status_code == 422
        _assert_envelope(res.json(), "insufficient_data")


class TestPortfolioRiskEndpoint:
    KEYS = {
        "symbols",
        "weights",
        "confidence",
        "var_pct",
        "es_pct",
        "portfolio_volatility",
        "undiversified_var",
        "component_var",
        "sharpe",
        "sortino",
        "n_obs",
        "asOf",
        "source",
        "cached",
    }

    def test_shape_and_cache(self, api):
        payload = {"weights": {"INFY": 0.6, "TCS": 0.4}, "confidence": 0.99}
        res = api.post("/api/v1/analytics/portfolio/risk", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert set(body) == self.KEYS
        assert body["cached"] is False
        assert set(body["component_var"]) == {"INFY", "TCS"}
        assert sum(body["component_var"].values()) == pytest.approx(body["var_pct"], rel=1e-9)
        assert body["es_pct"] > body["var_pct"]

        res2 = api.post("/api/v1/analytics/portfolio/risk", json=payload)
        assert res2.json()["cached"] is True

    def test_weights_not_summing_to_one_400(self, api):
        res = api.post(
            "/api/v1/analytics/portfolio/risk",
            json={"weights": {"INFY": 0.6, "TCS": 0.2}},
        )
        assert res.status_code == 400
        body = res.json()
        _assert_envelope(body, "bad_request")
        assert "sum to 1" in body["error"]["message"]

    def test_unknown_symbol_404(self, api):
        res = api.post(
            "/api/v1/analytics/portfolio/risk",
            json={"weights": {"INFY": 0.6, "NOPE": 0.4}},
        )
        assert res.status_code == 404
        _assert_envelope(res.json(), "not_found")

    def test_malformed_body_422(self, api):
        res = api.post("/api/v1/analytics/portfolio/risk", json={"weights": "INFY"})
        assert res.status_code == 422
        _assert_envelope(res.json(), "validation_error")


class TestBacktestEndpoint:
    KEYS = {
        "symbol",
        "method",
        "confidence",
        "window",
        "n_obs",
        "exceptions",
        "exception_rate",
        "expected_exceptions",
        "kupiec",
        "christoffersen",
        "basel_zone",
        "asOf",
        "source",
        "cached",
    }

    def test_shape_and_cache(self, api):
        res = api.get("/api/v1/analytics/backtest/var", params={"symbol": "INFY"})
        assert res.status_code == 200
        body = res.json()
        assert set(body) == self.KEYS
        assert set(body["kupiec"]) == {"lr", "p_value", "decision"}
        assert body["basel_zone"] in ("green", "amber", "red")
        assert body["n_obs"] == 400 - 250  # returns minus estimation window
        assert 0 <= body["exceptions"] <= body["n_obs"]
        assert body["cached"] is False

        second = api.get("/api/v1/analytics/backtest/var", params={"symbol": "INFY"})
        body2 = second.json()
        assert body2["cached"] is True
        assert {k: v for k, v in body2.items() if k != "cached"} == {
            k: v for k, v in body.items() if k != "cached"
        }

    def test_unknown_symbol_404(self, api):
        res = api.get("/api/v1/analytics/backtest/var", params={"symbol": "NOPE"})
        assert res.status_code == 404
        _assert_envelope(res.json(), "not_found")

    def test_insufficient_data_422(self, api):
        res = api.get("/api/v1/analytics/backtest/var", params={"symbol": "SHORT"})
        assert res.status_code == 422
        _assert_envelope(res.json(), "insufficient_data")


class TestAuth:
    def test_bearer_token_enforced(self, tmp_path, monkeypatch):
        with monkeypatch.context() as m:
            m.setenv("BAZZAR_DATA_DIR", str(tmp_path))
            m.setenv("BAZZAR_API_TOKEN", "test-token")
            get_settings.cache_clear()
            from backend.server import app

            with TestClient(app) as client:
                res = client.get("/api/v1/analytics/var", params={"symbol": "INFY"})
                assert res.status_code == 401
                _assert_envelope(res.json(), "unauthorized")
        get_settings.cache_clear()
