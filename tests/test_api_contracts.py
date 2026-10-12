"""P5 (roadmap 5.3): API contract hardening tests.

Covers the single error envelope, the X-Request-ID middleware, the /api/v1
mount + deprecated /api alias, CORS lockdown, and the exact response-shape
keys of the main GET endpoints (backend/schemas.py response models).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.settings import get_settings


@pytest.fixture()
def api(tmp_path, monkeypatch):
    with monkeypatch.context() as m:
        m.setenv("BAZZAR_DATA_DIR", str(tmp_path))
        m.delenv("BAZZAR_API_TOKEN", raising=False)
        get_settings.cache_clear()
        from backend.server import app

        with TestClient(app) as client:
            yield client
    get_settings.cache_clear()


# --- error envelope ----------------------------------------------------------


def _assert_envelope(body, code):
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == code
    assert isinstance(body["error"]["message"], str) and body["error"]["message"]


def test_404_envelope(api):
    res = api.get("/api/v1/definitely-not-a-route")
    assert res.status_code == 404
    _assert_envelope(res.json(), "not_found")


def test_404_chart_envelope(api):
    res = api.get("/api/v1/indices/NOPE/chart.png")
    assert res.status_code == 404
    _assert_envelope(res.json(), "not_found")


def test_422_validation_envelope(api):
    res = api.get("/api/v1/meta/rejects", params={"limit": 0})
    assert res.status_code == 422
    _assert_envelope(res.json(), "validation_error")


def test_503_envelope(api):
    """Kite login-url without a configured key is a 503 in the envelope."""
    res = api.get("/api/v1/auth/kite/login-url")
    assert res.status_code == 503
    _assert_envelope(res.json(), "service_unavailable")


def test_500_envelope_direct():
    """The catch-all handler maps unknown exceptions to the 500 envelope and
    never leaks internals (exercised directly; TestClient re-raises)."""
    import asyncio
    from types import SimpleNamespace

    from backend.server import _unhandled_exception_handler

    request = SimpleNamespace(state=SimpleNamespace(request_id="req-123"))
    response = asyncio.run(_unhandled_exception_handler(request, RuntimeError("secret internals")))
    assert response.status_code == 500
    import json

    body = json.loads(bytes(response.body))
    _assert_envelope(body, "internal_error")
    assert "secret internals" not in body["error"]["message"]
    assert "req-123" in body["error"]["message"]


# --- request id ----------------------------------------------------------------


def test_request_id_header_generated(api):
    res = api.get("/api/v1/health")
    rid = res.headers.get("x-request-id")
    assert rid and len(rid) == 32  # uuid4 hex


def test_request_id_echoed_when_supplied(api):
    res = api.get("/api/v1/health", headers={"X-Request-ID": "fixed-test-id"})
    assert res.headers["x-request-id"] == "fixed-test-id"


# --- /api/v1 mount + deprecated /api alias -------------------------------------


def test_v1_and_alias_agree(api):
    v1 = api.get("/api/v1/indices")
    alias = api.get("/api/indices")
    assert v1.status_code == alias.status_code == 200
    assert v1.json() == alias.json()


def test_alias_not_in_openapi_schema(api):
    paths = api.get("/openapi.json").json()["paths"]
    assert any(p.startswith("/api/v1/") for p in paths)
    assert not any(p.startswith("/api/health") for p in paths if "/v1/" not in p)


# --- CORS lockdown (P5, roadmap 5.2) -------------------------------------------


def test_cors_allows_vite_dev_origin(api):
    res = api.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_allows_packaged_null_origin(api):
    res = api.get("/api/v1/health", headers={"Origin": "null"})
    assert res.headers.get("access-control-allow-origin") == "null"


def test_cors_rejects_other_origins(api):
    res = api.get("/api/v1/health", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in res.headers


def test_cors_preflight(api):
    res = api.options(
        "/api/v1/indices",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res.status_code == 200
    assert "authorization" in res.headers["access-control-allow-headers"].lower()


# --- response-shape contracts ----------------------------------------------------


def test_indices_shape(api):
    rows = api.get("/api/v1/indices").json()
    assert isinstance(rows, list) and rows
    for row in rows:
        assert set(row) == {
            "symbol",
            "name",
            "exchange",
            "open",
            "high",
            "low",
            "close",
            "yearHigh",
            "yearLow",
            "asOf",
        }


def test_home_indices_shape(api):
    rows = api.get("/api/v1/home/indices").json()
    assert isinstance(rows, list) and rows
    for row in rows:
        assert set(row) == {"name", "symbol", "value", "change", "changePct", "asOf"}


def test_macro_shape(api):
    rows = api.get("/api/v1/macro").json()
    assert isinstance(rows, list) and rows
    for row in rows:
        assert set(row) == {
            "key",
            "title",
            "category",
            "unit",
            "frequency",
            "source",
            "sourceUrl",
            "latest",
            "period",
            "change",
        }


def test_benchmarks_shape(api):
    body = api.get("/api/v1/benchmarks").json()
    assert set(body) == {"groups"}
    assert body["groups"]
    for group in body["groups"]:
        assert set(group) == {"key", "title", "unit", "series"}
        for series in group["series"]:
            assert set(series) == {"name", "latest", "change", "asOf"}


def test_kite_status_shape(api, monkeypatch):
    # No OS keyring in CI: substitute the in-memory double (as in
    # tests/test_kite_auth.py) so the status endpoint can read config state.
    import backend.kite_auth as kite_auth
    from tests.test_kite_auth import FakeKeyring

    monkeypatch.setattr(kite_auth, "keyring", FakeKeyring())
    body = api.get("/api/v1/auth/kite/status").json()
    assert set(body) == {
        "configured",
        "api_key_set",
        "authenticated",
        "user",
        "login_time",
        "expires_hint",
    }
    # Non-secret contract: never tokens or the API secret.
    assert "access_token" not in body and "secret" not in body


def test_health_shape(api):
    body = api.get("/api/v1/health").json()
    assert set(body) == {"ok", "db", "version"}
    assert body["ok"] is True


def test_health_data_shape(api):
    body = api.get("/api/v1/health/data").json()
    assert set(body) == {"status", "checks", "summary", "asOf"}
    assert body["status"] == "green"


def test_search_shape(api):
    rows = api.get("/api/v1/search", params={"q": "nifty"}).json()
    for row in rows:
        assert set(row) == {"symbol", "name", "exchange"}


def test_quotes_shape(api):
    body = api.get("/api/v1/quotes", params={"symbols": "NIFTY 50"}).json()
    assert set(body) == {"symbols"}
    quote = body["symbols"]["NIFTY 50"]
    assert quote is None or set(quote) == {"value", "change", "changePct", "asOf"}
