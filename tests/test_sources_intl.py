"""P4-A: international benchmark source fetcher (backend.sources.intl).

Parser tests run fully offline against recorded fixtures in
tests/fixtures/. Source/sync tests inject a FakeSession — no network.
"""

from __future__ import annotations

import json
import time
import types
from pathlib import Path

import pytest
import requests

from backend.db import get_connection, initialize_database
from backend.sources import intl

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeResponse:
    def __init__(self, status_code: int, text: str = ""):
        self.status_code = status_code
        self.text = text
        self.content = text.encode("utf-8")
        self.headers: dict = {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    """Test double for requests.Session (GET-only; no network)."""

    def __init__(self, responses: list[FakeResponse]):
        self.headers: dict = {}
        self.responses = list(responses)
        self.calls: list[dict] = []

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params})
        return self.responses.pop(0)


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    initialize_database()
    con = get_connection()
    yield con
    con.close()


def _settings(monkeypatch, fred_api_key: str):
    """Deterministic settings stub (no dependence on real env / .env)."""
    monkeypatch.setattr(
        intl, "get_settings", lambda: types.SimpleNamespace(fred_api_key=fred_api_key)
    )


# --- parse_treasury_csv (pure, offline) --------------------------------------


def test_parse_treasury_csv_new_bc_columns():
    obs = intl.parse_treasury_csv(load_fixture("treasury_yield_curve_new.csv"))
    assert obs == [
        {"date": "2026-09-02", "value": 4.12},
        {"date": "2026-09-03", "value": 4.15},
    ]  # the blank BC_10YEAR cell on 09/04 is dropped, never defaulted


def test_parse_treasury_csv_legacy_columns():
    obs = intl.parse_treasury_csv(load_fixture("treasury_yield_curve_old.csv"))
    assert obs == [
        {"date": "2022-01-02", "value": 1.93},
        {"date": "2022-01-03", "value": 1.96},
        {"date": "2022-01-04", "value": 2.01},
    ]


def test_parse_treasury_csv_missing_10y_column_errors():
    with pytest.raises(intl.SourceError, match="10Y"):
        intl.parse_treasury_csv("Date,BC_5YEAR\n09/02/2026,3.85\n")


# --- parse_fred_observations (pure, offline) ---------------------------------


def test_parse_fred_observations_drops_missing():
    payload = json.loads(load_fixture("fred_fedfunds.json"))
    obs = intl.parse_fred_observations(payload)
    assert obs == [
        {"date": "2026-06-01", "value": 4.42},
        {"date": "2026-07-01", "value": 4.42},
        {"date": "2026-08-01", "value": 4.23},
    ]  # the "." observation for 2026-09 is dropped, never defaulted


# --- IntlSource HTTP behaviour (FakeSession) ----------------------------------


def test_fetch_us_10y_builds_year_url():
    session = FakeSession([FakeResponse(200, load_fixture("treasury_yield_curve_new.csv"))])
    source = intl.IntlSource(session=session)
    obs = source.fetch_us_10y(2026)
    assert len(obs) == 2
    assert "/2026/all" in session.calls[0]["url"]
    assert "daily_treasury_yield_curve" in session.calls[0]["url"]


def test_fetch_retries_429_then_succeeds(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    session = FakeSession(
        [
            FakeResponse(429, "slow down"),
            FakeResponse(200, load_fixture("treasury_yield_curve_old.csv")),
        ]
    )
    source = intl.IntlSource(session=session)
    obs = source.fetch_us_10y(2022)
    assert len(obs) == 3
    assert len(session.calls) == 2


def test_fetch_fed_funds_uses_config_series_id():
    session = FakeSession([FakeResponse(200, load_fixture("fred_fedfunds.json"))])
    source = intl.IntlSource(session=session)
    obs = source.fetch_fed_funds("test-key")
    assert len(obs) == 3
    params = session.calls[0]["params"]
    assert params == {"series_id": "FEDFUNDS", "api_key": "test-key", "file_type": "json"}


# --- sync (DuckDB, tmp data dir) ----------------------------------------------


def test_sync_writes_both_benchmarks(db, monkeypatch):
    _settings(monkeypatch, fred_api_key="test-key")
    session = FakeSession(
        [
            FakeResponse(200, load_fixture("treasury_yield_curve_new.csv")),
            FakeResponse(200, load_fixture("fred_fedfunds.json")),
        ]
    )
    summary = intl.sync(db, source=intl.IntlSource(session=session), year=2026)
    assert summary == {"us_10y": 2, "us_fed_funds": 3, "skipped": []}

    rows = db.execute(
        "SELECT date, value FROM benchmark_observations WHERE series_key = 'us_10y' ORDER BY date"
    ).fetchall()
    assert [(str(r[0]), r[1]) for r in rows] == [("2026-09-02", 4.12), ("2026-09-03", 4.15)]
    fed = db.execute(
        "SELECT date, value FROM benchmark_observations WHERE series_key = 'us_fed_funds'"
        " ORDER BY date"
    ).fetchall()
    assert [(str(r[0]), r[1]) for r in fed] == [
        ("2026-06-01", 4.42),
        ("2026-07-01", 4.42),
        ("2026-08-01", 4.23),
    ]

    run = db.execute(
        "SELECT status, rows_written FROM ingestion_runs WHERE job = ?", (intl.JOB,)
    ).fetchone()
    assert run == ("success", 5)


def test_sync_skips_fred_without_api_key(db, monkeypatch):
    _settings(monkeypatch, fred_api_key="")
    session = FakeSession([FakeResponse(200, load_fixture("treasury_yield_curve_new.csv"))])
    summary = intl.sync(db, source=intl.IntlSource(session=session), year=2026)
    assert summary["us_10y"] == 2
    assert summary["us_fed_funds"] is None
    assert summary["skipped"] == ["us_fed_funds"]
    assert len(session.calls) == 1  # FRED never called without a key
    n = db.execute(
        "SELECT COUNT(*) FROM benchmark_observations WHERE series_key = 'us_fed_funds'"
    ).fetchone()[0]
    assert n == 0  # nothing fabricated


def test_sync_treasury_failure_is_partial(db, monkeypatch):
    _settings(monkeypatch, fred_api_key="")
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    # 503 is retryable: the source retries with backoff, then gives up and the
    # sync records a partial run (remaining series still sync).
    session = FakeSession([FakeResponse(503, "unavailable") for _ in range(4)])
    summary = intl.sync(db, source=intl.IntlSource(session=session), year=2026)
    assert summary["us_10y"] == 0
    assert "us_10y" in summary["skipped"]
    run = db.execute(
        "SELECT status, error FROM ingestion_runs WHERE job = ?", (intl.JOB,)
    ).fetchone()
    assert run[0] == "partial"
    assert "us_10y" in run[1]
