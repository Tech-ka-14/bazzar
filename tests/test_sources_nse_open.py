"""P4-B: NSE open-data source (backend.sources.nse_open).

Parser tests run fully offline against recorded fixtures in
tests/fixtures/. Source/sync tests inject a FakeSession — no network.
"""

from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path

import pytest
import requests

from backend.calendar import is_trading_day
from backend.db import get_connection, initialize_database
from backend.sources import nse_open

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, status_code: int, payload: object = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = payload if isinstance(payload, str) else json.dumps(payload)

    def json(self):
        if isinstance(self._payload, str):
            return json.loads(self._payload)
        return self._payload

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


# --- parse_holiday_master (pure, offline) -----------------------------------------


def test_parse_holiday_master_cm_segment_only():
    payload = load_fixture("nse_holiday_master.json")
    rows = nse_open.parse_holiday_master(payload)  # default: CM only
    assert rows == [
        ("2026-01-26", False, "Republic Day"),
        ("2026-03-03", False, "Holi"),
        # Muhurat is a special TRADING session (official bars exist) — the
        # seeded calendar marks it is_trading_day=1; the sync must not flip it.
        ("2026-11-08", True, "Diwali Muhurat Trading"),
        ("2026-12-31", False, "New Year Eve (special closure)"),
    ]  # the broken-date row is dropped; the SLB segment is not read


def test_parse_holiday_master_date_formats():
    payload = {
        "CM": [
            {"tradingDate": "26-Jan-2026", "description": "a"},
            {"tradingDate": "03-March-2026", "description": "b"},
            {"tradingDate": "2026-04-14", "description": "c"},
            {"tradingDate": "01/05/2026", "description": "d"},
        ]
    }
    dates = [d for d, _, _ in nse_open.parse_holiday_master(payload)]
    assert dates == ["2026-01-26", "2026-03-03", "2026-04-14", "2026-05-01"]


def test_parse_holiday_master_non_dict():
    assert nse_open.parse_holiday_master([]) == []
    assert nse_open.parse_holiday_master(None) == []


# --- parse_fii_dii_flows (pure, offline) -------------------------------------------


def test_parse_fii_dii_groups_by_date():
    payload = load_fixture("nse_fiidii.json")
    flows = nse_open.parse_fii_dii_flows(payload)
    assert flows == [
        {"date": "2026-10-09", "fii_net": -2211.22, "dii_net": 2222.22},
        {"date": "2026-10-12", "fii_net": 1111.11, "dii_net": 1111.12},
        # the bogus-date row is dropped; the "-" net stays None (never defaulted)
        {"date": "2026-10-13", "fii_net": None, "dii_net": None},
    ]


# --- parse_index_constituents (pure, offline) --------------------------------------


def test_parse_index_constituents_drops_summary_row():
    payload = load_fixture("nse_equity_stock_indices.json")
    rows = nse_open.parse_index_constituents(payload)
    assert rows == [
        {"symbol": "RELIANCE", "name": "Reliance Industries Limited", "weight": 10.12},
        {"symbol": "HDFCBANK", "name": "HDFC Bank Limited", "weight": 9.87},
        {"symbol": "TCS", "name": "Tata Consultancy Services Limited"},  # no weight -> no key
    ]


# --- NseOpenSource HTTP behaviour (FakeSession) -------------------------------------


def test_bootstrap_cookies_before_first_api_call():
    session = FakeSession(
        [FakeResponse(200, "<html>ok</html>"), FakeResponse(200, load_fixture("nse_fiidii.json"))]
    )
    source = nse_open.NseOpenSource(session=session)
    flows = source.fetch_fii_dii()
    assert len(flows) == 3
    bootstrap, api = session.calls
    assert bootstrap["url"] == "https://www.nseindia.com"
    assert api["url"] == "https://www.nseindia.com/api/fiidiiTradeReact"


def test_401_triggers_cookie_rebootstrap_and_retry():
    session = FakeSession(
        [
            FakeResponse(200, "<html>ok</html>"),  # initial bootstrap
            FakeResponse(401, "denied"),  # first API call: cookie expired
            FakeResponse(200, "<html>ok</html>"),  # re-bootstrap
            FakeResponse(200, load_fixture("nse_fiidii.json")),
        ]
    )
    source = nse_open.NseOpenSource(session=session)
    flows = source.fetch_fii_dii()
    assert len(flows) == 3
    assert [c["url"] for c in session.calls].count("https://www.nseindia.com") == 2


def test_fetch_retries_429_then_succeeds(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    session = FakeSession(
        [
            FakeResponse(200, "<html>ok</html>"),
            FakeResponse(429, "slow down"),
            FakeResponse(200, load_fixture("nse_holiday_master.json")),
        ]
    )
    source = nse_open.NseOpenSource(session=session)
    holidays = source.fetch_holidays()
    assert len(holidays) == 4


# --- index constituents cache (tmp data dir) ----------------------------------------


def _constituents_session() -> FakeSession:
    return FakeSession(
        [
            FakeResponse(200, "<html>ok</html>"),
            FakeResponse(200, load_fixture("nse_equity_stock_indices.json")),
        ]
    )


def test_index_constituents_caches_and_reuses(tmp_path):
    session = _constituents_session()
    source = nse_open.NseOpenSource(session=session, cache_dir=tmp_path / "cache" / "nse")
    rows = source.index_constituents("NIFTY 50")
    assert [r["symbol"] for r in rows] == ["RELIANCE", "HDFCBANK", "TCS"]

    # second call: served from cache — no further HTTP
    cached = source.index_constituents("NIFTY 50")
    assert cached == rows
    assert len(session.calls) == 2

    # a fresh source with a failing session reuses the (still fresh) cache
    dead = nse_open.NseOpenSource(session=FakeSession([]), cache_dir=tmp_path / "cache" / "nse")
    assert dead.index_constituents("NIFTY 50") == rows


def test_index_constituents_failure_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    session = FakeSession([FakeResponse(200, "<html>ok</html>")] + [FakeResponse(503, "down")] * 4)
    source = nse_open.NseOpenSource(session=session, cache_dir=tmp_path / "cache" / "nse")
    assert source.index_constituents("NIFTY 50") == []


def test_index_constituents_stale_cache_used_on_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    cache_dir = tmp_path / "cache" / "nse"
    cache_dir.mkdir(parents=True)
    old = {
        "fetched_at": (dt.datetime.now(dt.UTC) - dt.timedelta(hours=48))
        .replace(tzinfo=None)
        .isoformat(),
        "rows": [{"symbol": "STALE", "name": "Stale Co"}],
    }
    (cache_dir / "index_constituents_nifty_50.json").write_text(json.dumps(old))

    session = FakeSession([FakeResponse(200, "<html>ok</html>")] + [FakeResponse(503, "down")] * 4)
    source = nse_open.NseOpenSource(session=session, cache_dir=cache_dir)
    assert source.index_constituents("NIFTY 50") == [{"symbol": "STALE", "name": "Stale Co"}]


# --- sync (DuckDB, tmp data dir) -----------------------------------------------------


def _nse_session() -> FakeSession:
    return FakeSession(
        [
            FakeResponse(200, "<html>ok</html>"),  # cookie bootstrap
            FakeResponse(200, load_fixture("nse_holiday_master.json")),
            FakeResponse(200, load_fixture("nse_fiidii.json")),
        ]
    )


def test_sync_writes_holidays_and_flows(db):
    summary = nse_open.sync(db, source=nse_open.NseOpenSource(session=_nse_session()))
    assert summary == {"holidays": 4, "fii_dii": 3, "skipped": []}

    # holiday semantics: seeded weekday flipped to non-trading by the sync
    assert is_trading_day(db, "2026-12-31") is False  # seeded trading day
    assert is_trading_day(db, "2026-01-26") is False
    assert is_trading_day(db, "2026-03-03") is False
    # Muhurat stays a trading day (special session), as in the seed CSV
    assert is_trading_day(db, "2026-11-08") is True

    rows = db.execute(
        "SELECT series_key, date, value FROM benchmark_observations"
        " WHERE series_key IN ('fii_net', 'dii_net') ORDER BY date, series_key"
    ).fetchall()
    assert [(r[0], str(r[1]), r[2]) for r in rows] == [
        ("dii_net", "2026-10-09", 2222.22),
        ("fii_net", "2026-10-09", -2211.22),
        ("dii_net", "2026-10-12", 1111.12),
        ("fii_net", "2026-10-12", 1111.11),
    ]  # the None-net 13-Oct row writes nothing


def test_sync_is_idempotent(db):
    nse_open.sync(db, source=nse_open.NseOpenSource(session=_nse_session()))
    nse_open.sync(db, source=nse_open.NseOpenSource(session=_nse_session()))
    assert db.execute("SELECT COUNT(*) FROM benchmark_observations").fetchone()[0] == 4
    holidays = db.execute(
        "SELECT COUNT(*) FROM trading_calendar WHERE holiday_name = 'Holi' AND date = '2026-03-03'"
    ).fetchone()[0]
    assert holidays == 1


def test_sync_records_ingestion_audit_row(db):
    nse_open.sync(db, source=nse_open.NseOpenSource(session=_nse_session()))
    row = db.execute(
        "SELECT status, rows_written, error FROM ingestion_runs WHERE job = ?",
        (nse_open.JOB,),
    ).fetchone()
    assert row is not None
    assert row[0] == "success"
    assert row[1] == 8  # 4 calendar rows + 4 benchmark observations
    assert row[2] is None


def test_sync_partial_on_fii_dii_failure(db, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    session = FakeSession(
        [
            FakeResponse(200, "<html>ok</html>"),
            FakeResponse(200, load_fixture("nse_holiday_master.json")),
            FakeResponse(503, "down"),
            FakeResponse(503, "down"),
            FakeResponse(503, "down"),
            FakeResponse(503, "down"),
        ]
    )
    summary = nse_open.sync(db, source=nse_open.NseOpenSource(session=session))
    assert summary["holidays"] == 4
    assert summary["skipped"] == ["fii_dii"]
    row = db.execute(
        "SELECT status, error FROM ingestion_runs WHERE job = ?", (nse_open.JOB,)
    ).fetchone()
    assert row[0] == "partial"
    assert "fii_dii" in row[1]
