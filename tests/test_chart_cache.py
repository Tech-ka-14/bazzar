"""P5 (roadmap 5.4): cache-first chart PNGs with an on-disk manifest.

Charts render once per data fingerprint under
``<BAZZAR_DATA_DIR>/cache/charts/<kind>/<key>_<paramhash>.png`` with a
``manifest.json`` alongside; unchanged data is served from cache, changed
data invalidates (never a stale chart, never a fabricated one).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.db import get_connection
from backend.settings import get_settings

ROWS = [
    ("NIFTY 50", "2026-10-09", 24100.0, 24200.0, 24050.0, 24150.5),
    ("NIFTY 50", "2026-10-10", 24160.0, 24300.0, 24100.0, 24250.25),
]


def _seed_index(con, rows=ROWS):
    for symbol, date, o, h, low, c in rows:
        con.execute(
            "INSERT INTO index_daily (symbol, date, open, high, low, close)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (symbol, date, o, h, low, c),
        )


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


def test_chart_404_envelope_without_data(api):
    client, _ = api
    res = client.get("/api/v1/indices/NIFTY 50/chart.png")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "not_found"


def test_chart_cached_and_manifest_written(api, monkeypatch):
    client, tmp_path = api
    with get_connection() as con:
        _seed_index(con)

    renders = 0
    import backend.server as server

    real_render = server.render_candles_png

    def counting_render(bars, title, out_path):
        nonlocal renders
        renders += 1
        return real_render(bars, title, out_path)

    monkeypatch.setattr(server, "render_candles_png", counting_render)

    res = client.get("/api/v1/indices/NIFTY 50/chart.png")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert renders == 1

    manifest_path = tmp_path / "cache" / "charts" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest) == 1
    rel, entry = next(iter(manifest.items()))
    assert rel.startswith("index/NIFTY_50_") and rel.endswith(".png")
    assert entry["kind"] == "index"
    assert entry["fingerprint"].startswith("2:2026-10-10:")
    assert (tmp_path / "cache" / "charts" / rel).exists()

    # Second call with unchanged data → cache hit, no re-render.
    res2 = client.get("/api/v1/indices/NIFTY 50/chart.png")
    assert res2.status_code == 200
    assert renders == 1
    assert res2.content == res.content

    # New data changes the fingerprint → exactly one re-render.
    with get_connection() as con:
        _seed_index(con, [("NIFTY 50", "2026-10-12", 24300.0, 24400.0, 24200.0, 24350.0)])
    res3 = client.get("/api/v1/indices/NIFTY 50/chart.png")
    assert res3.status_code == 200
    assert renders == 2


def test_stock_chart_params_separate_cache_entries(api):
    client, tmp_path = api
    with get_connection() as con:
        for exchange in ("NSE", "BSE"):
            con.execute(
                "INSERT INTO daily_ohlcv (symbol, exchange, date, open, high, low, close, volume)"
                " VALUES ('INFY', ?, DATE '2026-10-10', 1500.0, 1520.0, 1490.0, 1510.0, 1000)",
                (exchange,),
            )
    assert (
        client.get("/api/v1/stocks/INFY/chart.png", params={"exchange": "NSE"}).status_code == 200
    )
    assert (
        client.get("/api/v1/stocks/INFY/chart.png", params={"exchange": "BSE"}).status_code == 200
    )
    manifest = json.loads((tmp_path / "cache" / "charts" / "manifest.json").read_text())
    stock_entries = [k for k in manifest if k.startswith("stock/INFY_")]
    assert len(stock_entries) == 2  # one cache entry per exchange param


def test_cached_chart_png_unit(tmp_path, monkeypatch):
    """Direct unit test of the store: hit, miss, and corrupt-manifest rebuild."""
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    from backend.charts import cached_chart_png

    calls = []

    def render(path: Path) -> None:
        calls.append(str(path))
        path.write_bytes(b"png-bytes")

    p1 = cached_chart_png("index", "NIFTY 50", {}, "fp1", render)
    assert p1.read_bytes() == b"png-bytes"
    p2 = cached_chart_png("index", "NIFTY 50", {}, "fp1", render)
    assert p1 == p2 and len(calls) == 1  # fingerprint match → cache hit
    p3 = cached_chart_png("index", "NIFTY 50", {}, "fp2", render)
    assert p3 == p1 and len(calls) == 2  # fingerprint change → re-render

    # A corrupt manifest is rebuilt from scratch (re-render, no crash).
    (tmp_path / "cache" / "charts" / "manifest.json").write_text("{not json", encoding="utf-8")
    cached_chart_png("index", "NIFTY 50", {}, "fp2", render)
    assert len(calls) == 3
