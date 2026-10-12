"""P5 (roadmap 5.5): liveness (/api/health) vs readiness (/api/health/ready).

Liveness answers 200 whenever the process serves; readiness additionally
requires DuckDB to open, migrations to be at latest, and the data dir to be
writable — else 503 in the standard error envelope.
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


def test_ready_when_healthy(api):
    res = api.get("/api/v1/health/ready")
    assert res.status_code == 200
    body = res.json()
    assert set(body) == {"status", "db", "version"}
    assert body["status"] == "ready"


def test_ready_on_deprecated_alias(api):
    assert api.get("/api/health/ready").status_code == 200


def test_unready_with_unwritable_data_dir(tmp_path, monkeypatch):
    """Point BAZZAR_DATA_DIR at a regular file: not writable as a directory
    and DuckDB cannot open beneath it. Liveness still answers 200 (ok=false)
    while readiness returns the 503 envelope."""
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("occupied", encoding="utf-8")
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(blocker))
    monkeypatch.delenv("BAZZAR_API_TOKEN", raising=False)
    get_settings.cache_clear()
    from backend.server import app

    # No startup (would fail loudly by design) — TestClient without the
    # context manager skips lifespan events but serves requests.
    client = TestClient(app)
    try:
        live = client.get("/api/v1/health")
        assert live.status_code == 200
        assert live.json()["ok"] is False

        ready = client.get("/api/v1/health/ready")
        assert ready.status_code == 503
        body = ready.json()
        assert set(body) == {"error"}
        assert body["error"]["code"] == "service_unavailable"
        assert "not ready" in body["error"]["message"]
    finally:
        get_settings.cache_clear()
