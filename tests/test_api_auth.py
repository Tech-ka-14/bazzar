"""P5 (roadmap 5.1): localhost bearer-token handshake.

When BAZZAR_API_TOKEN is set, every /api/* request must carry a matching
``Authorization: Bearer <token>`` header; when unset (plain dev run) the API
is open. The Kite redirect callback is the single exemption (the external
browser is redirected there by kite.trade and cannot know the token).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.settings import get_settings

TOKEN = "p5-test-token-" + "ab" * 16


@pytest.fixture()
def authed_api(tmp_path, monkeypatch):
    with monkeypatch.context() as m:
        m.setenv("BAZZAR_DATA_DIR", str(tmp_path))
        m.setenv("BAZZAR_API_TOKEN", TOKEN)
        get_settings.cache_clear()
        from backend.server import app

        with TestClient(app) as client:
            yield client
    get_settings.cache_clear()


@pytest.fixture()
def open_api(tmp_path, monkeypatch):
    with monkeypatch.context() as m:
        m.setenv("BAZZAR_DATA_DIR", str(tmp_path))
        m.delenv("BAZZAR_API_TOKEN", raising=False)
        get_settings.cache_clear()
        from backend.server import app

        with TestClient(app) as client:
            yield client
    get_settings.cache_clear()


def test_missing_token_is_401_with_envelope(authed_api):
    res = authed_api.get("/api/v1/indices")
    assert res.status_code == 401
    assert res.headers["www-authenticate"] == "Bearer"
    assert set(res.json()) == {"error"}
    assert res.json()["error"]["code"] == "unauthorized"


def test_wrong_token_is_401(authed_api):
    res = authed_api.get("/api/v1/indices", headers={"Authorization": "Bearer wrong"})
    assert res.status_code == 401


def test_health_is_protected_too(authed_api):
    assert authed_api.get("/api/v1/health").status_code == 401
    assert authed_api.get("/api/health").status_code == 401


def test_correct_token_is_200(authed_api):
    for path in ("/api/v1/health", "/api/v1/indices", "/api/indices"):
        res = authed_api.get(path, headers={"Authorization": f"Bearer {TOKEN}"})
        assert res.status_code == 200, path


def test_kite_callback_exempt_from_bearer(authed_api):
    """The external-browser Kite redirect cannot carry the token; the
    one-time request_token is itself the credential. Missing/empty token is
    a 400 (never a 401)."""
    res = authed_api.get("/api/v1/auth/kite/callback")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "bad_request"
    res = authed_api.get("/api/auth/kite/callback")
    assert res.status_code == 400


def test_unset_token_opens_api(open_api):
    res = open_api.get("/api/v1/indices")
    assert res.status_code == 200
