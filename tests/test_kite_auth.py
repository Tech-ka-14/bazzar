"""P3: Kite auth store tests — OS keyring wrappers (fake keyring), session
exchange, and the /api/auth/kite/* endpoints. No real keyring, no network.
"""

from __future__ import annotations

import keyring as real_keyring
import pytest
from fastapi.testclient import TestClient

import backend.kite_auth as kite_auth
from backend.kite_auth import KeyringUnavailable
from backend.providers.base import ProviderError
from backend.providers.kite import KiteAuthRequired
from backend.settings import get_settings


class FakeKeyring:
    """In-memory keyring double mirroring the real keyring API surface."""

    class errors:
        KeyringError = real_keyring.errors.KeyringError
        PasswordDeleteError = real_keyring.errors.PasswordDeleteError

    def __init__(self):
        self.store: dict[tuple[str, str], str] = {}

    def set_password(self, service, key, value):
        self.store[(service, key)] = value

    def get_password(self, service, key):
        return self.store.get((service, key))

    def delete_password(self, service, key):
        if (service, key) not in self.store:
            raise self.errors.PasswordDeleteError("not found")
        del self.store[(service, key)]


@pytest.fixture()
def fake_keyring(monkeypatch):
    fake = FakeKeyring()
    monkeypatch.setattr(kite_auth, "keyring", fake)
    return fake


# --- keyring wrappers ------------------------------------------------------------


def test_secret_and_session_roundtrip(fake_keyring):
    kite_auth.store_api_secret("s3cret")
    assert kite_auth.get_api_secret() == "s3cret"
    kite_auth.store_session("access-token", {"user_id": "AB1234"})
    assert kite_auth.get_access_token() == "access-token"
    meta = kite_auth.get_session_meta()
    assert meta["user_id"] == "AB1234"
    assert meta["login_time"]  # ISO timestamp stamped on store


def test_clear_session_keeps_secret(fake_keyring):
    kite_auth.store_api_secret("s3cret")
    kite_auth.store_session("access-token")
    kite_auth.clear_session()
    assert kite_auth.get_access_token() is None
    assert kite_auth.get_session_meta() == {}
    assert kite_auth.get_api_secret() == "s3cret"  # secret survives logout


def test_clear_session_is_idempotent(fake_keyring):
    kite_auth.clear_session()  # nothing stored — must not raise


def test_empty_values_refused(fake_keyring):
    with pytest.raises(ProviderError, match="empty"):
        kite_auth.store_api_secret("   ")
    with pytest.raises(ProviderError, match="empty"):
        kite_auth.store_session("")


def test_keyring_unavailable_wraps_errors(monkeypatch):
    class BrokenKeyring(FakeKeyring):
        def get_password(self, service, key):
            raise self.errors.KeyringError("no backend")

    monkeypatch.setattr(kite_auth, "keyring", BrokenKeyring())
    with pytest.raises(KeyringUnavailable):
        kite_auth.get_access_token()


def test_status_never_contains_secrets(fake_keyring):
    kite_auth.store_api_secret("super-secret-value")
    kite_auth.store_session("super-secret-token", {"user_id": "AB1234"})
    status = kite_auth.auth_status("kite-key")
    text = repr(status)
    assert "super-secret-value" not in text
    assert "super-secret-token" not in text
    assert status == {
        "configured": True,
        "api_key_set": True,
        "authenticated": True,
        "user": "AB1234",
        "login_time": status["login_time"],
        "expires_hint": status["expires_hint"],
    }


def test_status_unconfigured(fake_keyring):
    status = kite_auth.auth_status("")
    assert status["configured"] is False
    assert status["api_key_set"] is False
    assert status["authenticated"] is False
    assert status["user"] is None


# --- session exchange -------------------------------------------------------------


class FakeSessionClient:
    def __init__(self):
        self.calls = []

    def generate_session(self, request_token, api_secret=None):
        self.calls.append({"request_token": request_token, "api_secret": api_secret})
        return {
            "access_token": "AT",
            "user_id": "AB1234",
            "user_name": "Test User",
        }


def test_exchange_request_token_stores_session(fake_keyring):
    kite_auth.store_api_secret("s3cret")
    client = FakeSessionClient()
    meta = kite_auth.exchange_request_token("kite-key", "req-123", client=client)
    assert client.calls == [{"request_token": "req-123", "api_secret": "s3cret"}]
    assert meta == {"user_id": "AB1234", "user_name": "Test User"}
    assert kite_auth.get_access_token() == "AT"
    assert kite_auth.get_session_meta()["user_id"] == "AB1234"


def test_exchange_requires_secret(fake_keyring):
    with pytest.raises(KiteAuthRequired, match="set-secret"):
        kite_auth.exchange_request_token("kite-key", "req-123", client=FakeSessionClient())


def test_exchange_failure_is_provider_error(fake_keyring):
    class FailingClient:
        def generate_session(self, request_token, api_secret=None):
            raise RuntimeError("checksum mismatch")

    kite_auth.store_api_secret("s3cret")
    with pytest.raises(ProviderError, match="exchange failed"):
        kite_auth.exchange_request_token("kite-key", "req-123", client=FailingClient())
    assert kite_auth.get_access_token() is None  # nothing stored on failure


# --- API endpoints ------------------------------------------------------------------


@pytest.fixture()
def api(tmp_path, monkeypatch, fake_keyring):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("KITE_API_KEY", "kite-key")
    get_settings.cache_clear()
    from backend.server import app

    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()


def test_login_url_endpoint(api):
    res = api.get("/api/auth/kite/login-url")
    assert res.status_code == 200
    assert res.json() == {"url": "https://kite.trade/connect/login?api_key=kite-key&v=3"}


def test_status_endpoint(api):
    res = api.get("/api/auth/kite/status")
    assert res.status_code == 200
    body = res.json()
    assert body["api_key_set"] is True
    assert body["authenticated"] is False
    assert set(body) == {
        "configured",
        "api_key_set",
        "authenticated",
        "user",
        "login_time",
        "expires_hint",
    }  # no token/secret fields ever


def test_callback_endpoint_exchanges_and_stores(api, monkeypatch):
    original = kite_auth.exchange_request_token
    client = FakeSessionClient()

    def fake_exchange(api_key, request_token):
        assert api_key == "kite-key"
        return original(api_key, request_token, client=client)

    monkeypatch.setattr(kite_auth, "exchange_request_token", fake_exchange)
    kite_auth.store_api_secret("s3cret")
    res = api.get("/api/auth/kite/callback", params={"request_token": "req-123"})
    assert res.status_code == 200
    assert res.json() == {
        "status": "connected",
        "user_id": "AB1234",
        "user_name": "Test User",
    }
    assert kite_auth.get_access_token() == "AT"  # session landed in the keyring


def test_callback_missing_token_is_400(api):
    res = api.get("/api/auth/kite/callback")
    assert res.status_code == 400


def test_disconnect_clears_session(api):
    kite_auth.store_api_secret("s3cret")
    kite_auth.store_session("AT")
    res = api.post("/api/auth/kite/disconnect")
    assert res.status_code == 200
    assert res.json() == {"status": "disconnected"}
    assert kite_auth.get_access_token() is None
    assert kite_auth.get_api_secret() == "s3cret"
