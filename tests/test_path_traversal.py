"""P6 (roadmap 6.4): path-traversal rejection on user-derived file paths.

Every endpoint that turns user input (symbol / key / kind) into a filesystem
path must route through ``backend.charts._sanitize_name`` (allowlist:
``[A-Za-z0-9_.-]``; everything else, including ``/`` ``\\`` and unicode
lookalikes, collapses to ``_``) so a crafted symbol can never escape the
chart cache directory. These tests pin both the sanitizer contract and the
end-to-end behaviour of the chart endpoints.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.charts import _sanitize_name, cached_chart_png
from backend.settings import get_settings

TRAVERSAL_INPUTS = [
    "../../etc/passwd",
    "..\\..\\windows\\system32",
    "../../../secret",
    "..",
    "...",
    "NIFTY/../../../tmp/evil",
    "/etc/passwd",
    "C:\\Windows\\System32",
    "a/./b/../c",
    "….\\….\\evil",  # unicode one-dot-leader lookalike
    "ＮＩＦＴＹ",  # fullwidth unicode — not in the allowlist
    "nul\x00injection",  # NUL byte
    "%2e%2e%2fetc",  # percent-encoding is NOT decoded by the sanitizer
]


@pytest.mark.parametrize("raw", TRAVERSAL_INPUTS)
def test_sanitize_name_never_escapes_directory(raw: str) -> None:
    safe = _sanitize_name(raw)
    assert "/" not in safe
    assert "\\" not in safe
    assert "\x00" not in safe
    assert safe not in {".", ".."}
    # The sanitized name is always a plain single path component.
    assert Path(safe).name == safe


@pytest.mark.parametrize("raw", TRAVERSAL_INPUTS)
def test_cached_chart_png_stays_inside_cache_root(tmp_path, monkeypatch, raw: str) -> None:
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        out = cached_chart_png(
            raw,  # kind is normally a server-side constant; abuse it anyway
            raw,
            {},
            "fp",
            lambda path: Path(path).write_bytes(b"\x89PNG"),
        )
        root = (tmp_path / "cache" / "charts").resolve()
        assert root in out.resolve().parents
    finally:
        get_settings.cache_clear()


@pytest.fixture()
def api(tmp_path, monkeypatch):
    with monkeypatch.context() as m:
        m.setenv("BAZZAR_DATA_DIR", str(tmp_path))
        m.delenv("BAZZAR_API_TOKEN", raising=False)
        get_settings.cache_clear()
        from backend.server import app

        with TestClient(app) as client:
            yield client, tmp_path
    get_settings.cache_clear()


def test_chart_endpoint_rejects_traversal_symbol(api) -> None:
    client, tmp_path = api
    # No data is seeded, so any symbol must 404 with the standard envelope —
    # and no chart PNG may be rendered (let alone outside the cache root).
    res = client.get("/api/v1/indices/..%2F..%2Fetc%2Fpasswd/chart.png")
    assert res.status_code in {404, 422}
    if res.headers.get("content-type", "").startswith("application/json"):
        assert "error" in res.json()
    assert list(tmp_path.rglob("*.png")) == []


def test_chart_endpoint_rejects_absolute_path_symbol(api) -> None:
    client, _ = api
    res = client.get("/api/v1/stocks/%2Fetc%2Fpasswd/chart.png")
    assert res.status_code in {404, 422}
