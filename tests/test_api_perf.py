"""P5 (roadmap 5.4): performance features — gzip, weak ETags, warm-path p95.

The p95 assertion uses a generous CI-safe bound (500ms); the measured value
is printed so the report can record the real warm number (acceptance target:
indices p95 < 50ms warm on dev hardware).
"""

from __future__ import annotations

import statistics
import time

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


def test_etag_200_then_304(api):
    res = api.get("/api/v1/indices")
    assert res.status_code == 200
    etag = res.headers.get("etag")
    assert etag and etag.startswith('W/"')

    res2 = api.get("/api/v1/indices", headers={"If-None-Match": etag})
    assert res2.status_code == 304
    assert res2.content == b""
    assert res2.headers.get("etag") == etag

    res3 = api.get("/api/v1/indices", headers={"If-None-Match": 'W/"bogus"'})
    assert res3.status_code == 200


def test_etag_on_macro_and_benchmarks(api):
    for path in ("/api/v1/macro", "/api/v1/benchmarks"):
        res = api.get(path)
        assert res.status_code == 200
        etag = res.headers.get("etag")
        assert etag, path
        res2 = api.get(path, headers={"If-None-Match": etag})
        assert res2.status_code == 304, path


def test_no_etag_on_chart_png(api):
    res = api.get("/api/v1/indices/NOPE/chart.png")
    assert res.status_code == 404  # never synced → 404, and no ETag semantics
    assert "etag" not in res.headers


def test_gzip_large_json(api):
    res = api.get("/api/v1/macro", headers={"Accept-Encoding": "gzip"})
    assert res.status_code == 200
    # The macro registry is well above the 1KB minimum_size.
    assert res.headers.get("content-encoding") == "gzip"
    assert isinstance(res.json(), list) and res.json()


def test_indices_warm_p95(api):
    """Warm-path latency check. The assertion bound (500ms) is deliberately
    CI-safe; the measured p95 is printed for the P5 report."""
    api.get("/api/v1/indices")  # warm up (view creation, imports)
    samples = []
    for _ in range(60):
        start = time.perf_counter()
        res = api.get("/api/v1/indices")
        assert res.status_code == 200
        samples.append(time.perf_counter() - start)
    p95 = statistics.quantiles(samples, n=20)[-1]
    median = statistics.median(samples)
    print(f"\n[perf] /api/v1/indices warm: median={median * 1000:.2f}ms p95={p95 * 1000:.2f}ms")
    assert p95 < 0.5, f"warm p95 {p95 * 1000:.1f}ms exceeds the CI-safe 500ms bound"
