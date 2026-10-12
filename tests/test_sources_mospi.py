"""P4-B: MoSPI/data.gov.in OGD source fetcher (backend.sources.mospi).

Parser tests run fully offline against recorded fixtures in
tests/fixtures/. Source/sync tests inject a FakeSession — no network.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
import requests

from backend.db import get_connection, initialize_database
from backend.settings import get_settings
from backend.sources import mospi

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


# --- parse_period (pure, offline) ----------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2025-01", "2025-01"),
        ("2025-1", "2025-01"),
        ("2025-01-15", "2025-01"),
        ("01/2025", "2025-01"),
        ("12-2025", "2025-12"),
        ("Jan 2025", "2025-01"),
        ("January-2025", "2025-01"),
        ("2025 Mar", "2025-03"),
        ("13/2025", None),
        ("nope", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_period_monthly(raw, expected):
    assert mospi.parse_period(raw, "monthly") == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2025-Q1", "2025-Q1"),
        ("2025Q3", "2025-Q3"),
        ("Q1 2025", "2025-Q1"),
        ("q2 2025", "2025-Q2"),
        ("Q1 2024-25", "2024-Q1"),
        ("Q4 FY2024", "2024-Q4"),
        ("Q5 2025", None),
        ("2025-01", None),
    ],
)
def test_parse_period_quarterly(raw, expected):
    assert mospi.parse_period(raw, "quarterly") == expected


# --- parse_ogd_records (pure, offline) -------------------------------------------


def test_parse_cpi_monthly_fixture():
    payload = load_fixture("ogd_cpi_monthly.json")
    obs = mospi.parse_ogd_records(
        payload,
        value_field=["inflation_rate", "value"],
        period_field=["period", "month"],
        period_format="monthly",
    )
    # the "N/A" value and the unparseable period are dropped, never defaulted
    assert obs == [
        {"period": "2026-01", "value": 4.31},
        {"period": "2026-02", "value": 3.87},
        {"period": "2026-04", "value": 3.55},
    ]


def test_parse_wpi_monthly_fixture():
    payload = load_fixture("ogd_wpi_monthly.json")
    obs = mospi.parse_ogd_records(
        payload,
        value_field=["wpi_inflation"],
        period_field=["month"],
        period_format="monthly",
    )
    assert obs == [
        {"period": "2026-01", "value": 1.84},
        {"period": "2026-02", "value": 2.13},
        {"period": "2026-04", "value": 2.05},
    ]


def test_parse_gdp_quarterly_fixture():
    payload = load_fixture("ogd_gdp_quarterly.json")
    obs = mospi.parse_ogd_records(
        payload,
        value_field=["value"],
        period_field=["period"],
        period_format="quarterly",
    )
    # "FY 2025" is not a quarter label -> dropped
    assert obs == [
        {"period": "2025-Q1", "value": 7.8},
        {"period": "2025-Q2", "value": 8.2},
        {"period": "2025-Q3", "value": 8.4},
    ]


def test_parse_case_insensitive_fields_and_dedup():
    rows = [
        {"Month": "Jan 2026", "Inflation_Rate": 4.0},
        {"month": "Jan 2026", "inflation_rate": 4.5},
        {"month": "Feb 2026", "inflation_rate": "3,912.10"},
    ]
    obs = mospi.parse_ogd_records(
        rows, value_field="inflation_rate", period_field="month", period_format="monthly"
    )
    assert obs == [
        {"period": "2026-01", "value": 4.5},  # last wins
        {"period": "2026-02", "value": 3912.10},  # thousands separators stripped
    ]


# --- MospiSource HTTP behaviour (FakeSession) ------------------------------------


def test_fetch_series_uses_config_url_and_key():
    session = FakeSession([FakeResponse(200, load_fixture("ogd_cpi_monthly.json"))])
    source = mospi.MospiSource(session=session, api_key="test-key")
    obs = source.fetch_series("cpi_inflation")
    assert [o["value"] for o in obs] == [4.31, 3.87, 3.55]
    (call,) = session.calls
    assert call["url"] == ("https://api.data.gov.in/resource/9d67b242-0243-4298-adf9-7617dbeba7ab")
    assert call["params"]["api-key"] == "test-key"
    assert call["params"]["format"] == "json"


def test_fetch_retries_429_then_succeeds(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    session = FakeSession(
        [FakeResponse(429, "slow down"), FakeResponse(200, load_fixture("ogd_wpi_monthly.json"))]
    )
    source = mospi.MospiSource(session=session, api_key="test-key")
    obs = source.fetch_series("wpi_inflation")
    assert len(obs) == 3
    assert len(session.calls) == 2  # failed attempt + retry


def test_fetch_empty_resource_id_raises_clear_error():
    source = mospi.MospiSource(session=FakeSession([]), api_key="test-key")
    with pytest.raises(mospi.SourceError, match="no OGD resource configured"):
        source.fetch_series("iip")  # documented gap
    with pytest.raises(KeyError):
        source.fetch_series("nope")


def test_fetch_without_api_key_raises():
    source = mospi.MospiSource(session=FakeSession([]), api_key=None)
    with pytest.raises(mospi.SourceError, match="OGD_API_KEY not set"):
        source.fetch_series("cpi_inflation")


# --- sync (DuckDB, tmp data dir) --------------------------------------------------


def _ogd_session() -> FakeSession:
    return FakeSession(
        [
            FakeResponse(200, load_fixture("ogd_cpi_monthly.json")),
            FakeResponse(200, load_fixture("ogd_wpi_monthly.json")),
        ]
    )


def test_sync_writes_macro_observations(db):
    summary = mospi.sync(db, source=mospi.MospiSource(session=_ogd_session(), api_key="k"))
    assert summary["synced"] == {"cpi_inflation": 3, "wpi_inflation": 3}
    # iip / gdp_growth have no OGD resource (documented gaps) -> skipped
    assert set(summary["skipped"]) == {"iip", "gdp_growth"}

    rows = db.execute(
        "SELECT period, value FROM macro_observations WHERE series_key = 'cpi_inflation'"
        " ORDER BY period"
    ).fetchall()
    assert rows == [("2026-01", 4.31), ("2026-02", 3.87), ("2026-04", 3.55)]


def test_sync_is_idempotent(db):
    mospi.sync(db, source=mospi.MospiSource(session=_ogd_session(), api_key="k"))
    mospi.sync(db, source=mospi.MospiSource(session=_ogd_session(), api_key="k"))
    n = db.execute("SELECT COUNT(*) FROM macro_observations").fetchone()[0]
    assert n == 6


def test_sync_records_ingestion_audit_row(db):
    mospi.sync(db, source=mospi.MospiSource(session=_ogd_session(), api_key="k"))
    row = db.execute(
        "SELECT status, rows_written, error FROM ingestion_runs WHERE job = ?",
        (mospi.JOB,),
    ).fetchone()
    assert row is not None
    assert row[0] == "partial"  # iip/gdp_growth skipped -> partial, not failed
    assert row[1] == 6
    assert "iip" in row[2]


def test_sync_skips_cleanly_without_api_key(db, monkeypatch):
    monkeypatch.setenv("OGD_API_KEY", "")
    get_settings.cache_clear()
    try:
        summary = mospi.sync(db)  # no source injected -> reads settings
    finally:
        get_settings.cache_clear()
    assert summary["synced"] == {}
    assert set(summary["skipped"]) == {
        "cpi_inflation",
        "wpi_inflation",
        "iip",
        "gdp_growth",
    }
    # nothing written, no ingestion run recorded (clean skip, never fabricate)
    assert db.execute("SELECT COUNT(*) FROM macro_observations").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM ingestion_runs").fetchone()[0] == 0
