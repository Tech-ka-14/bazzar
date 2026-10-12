"""P4-A: RBI DBIE source fetcher (backend.sources.rbi).

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
from backend.sources import rbi

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, status_code: int, text: str = "", headers: dict | None = None):
        self.status_code = status_code
        self.text = text
        self.content = text.encode("utf-8")
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    """Test double for requests.Session (POST-only; no network)."""

    def __init__(self, responses: list[FakeResponse]):
        self.headers: dict = {}
        self.responses = list(responses)
        self.calls: list[dict] = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return self.responses.pop(0)


def _gateway_payload(fixture_name: str) -> str:
    """Fixture JSON as the gateway serves it: HTML-entity-encoded."""
    return json.dumps(load_fixture(fixture_name)).replace('"', "&quot;")


def _token_response() -> FakeResponse:
    return FakeResponse(
        200, '{"body": {"status": "ok"}}', headers={"authorization": "Bearer guest-token"}
    )


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    initialize_database()
    con = get_connection()
    yield con
    con.close()


# --- parse_dbie_series (pure, offline) --------------------------------------


def test_parse_gsec_filters_10y_slice():
    payload = load_fixture("rbi_dbie_gsec_yield.json")
    obs = rbi.parse_dbie_series(
        payload, dimension_column="mat_per_rn_description", dimension_values=["10"]
    )
    assert obs == [
        {"date": "2026-07-01", "value": 7.0231},
        {"date": "2026-08-01", "value": 6.9902},
    ]  # the null-valued 2026-09 row is dropped, never defaulted


def test_parse_gsec_filters_5y_slice():
    payload = load_fixture("rbi_dbie_gsec_yield.json")
    obs = rbi.parse_dbie_series(
        payload, dimension_column="mat_per_rn_description", dimension_values=["5"]
    )
    assert [o["value"] for o in obs] == [6.8123, 6.7754]


def test_parse_tbill_matches_dimension_code_or_label():
    payload = load_fixture("rbi_dbie_tbill_yield.json")
    obs = rbi.parse_dbie_series(
        payload,
        dimension_column="mat_term_d_rn_description",
        dimension_values=["15TO91", "15-91 days"],
    )
    assert obs == [
        {"date": "2026-08-01", "value": 6.4891},
        {"date": "2026-09-01", "value": 6.5134},
    ]
    other = rbi.parse_dbie_series(
        payload,
        dimension_column="mat_term_d_rn_description",
        dimension_values=["92-182 days"],
    )
    assert [o["value"] for o in other] == [6.612]


def test_parse_forex_total_component_only():
    payload = load_fixture("rbi_dbie_forex_reserves.json")
    obs = rbi.parse_dbie_series(
        payload,
        dimension_column="typ_maj_fr_exc_res_rn_description",
        dimension_values=["FER_TTL", "Foreign Exchange Reserves"],
    )
    assert obs == [
        {"date": "2026-09-12", "value": 641235.5},
        {"date": "2026-09-19", "value": 642518.9},
    ]


def test_parse_date_formats():
    rows = [
        {"TIME_PERIOD": "2026-08-15", "OBS_VALUE": 1.0},
        {"TIME_PERIOD": "2026-08", "OBS_VALUE": 2.0},
        {"TIME_PERIOD": "15-09-2026", "OBS_VALUE": 3.0},
        {"TIME_PERIOD": "2026", "OBS_VALUE": 4.0},
        {"TIME_PERIOD": "not-a-date", "OBS_VALUE": 5.0},
        {"TIME_PERIOD": "2026-07", "OBS_VALUE": "N/A"},
    ]
    obs = rbi.parse_dbie_series(rows)
    assert obs == [
        {"date": "2026-01-01", "value": 4.0},
        {"date": "2026-08-01", "value": 2.0},
        {"date": "2026-08-15", "value": 1.0},
        {"date": "2026-09-15", "value": 3.0},
    ]


def test_parse_deduplicates_last_wins():
    rows = [
        {"TIME_PERIOD": "2026-08", "OBS_VALUE": 1.0},
        {"TIME_PERIOD": "2026-08", "OBS_VALUE": 2.0},
    ]
    assert rbi.parse_dbie_series(rows) == [{"date": "2026-08-01", "value": 2.0}]


def test_decode_payload_unescapes_entities():
    resp = FakeResponse(200, _gateway_payload("rbi_dbie_tbill_yield.json"))
    payload = rbi.RbiSource._decode_payload(resp)
    obs = rbi.parse_dbie_series(
        payload,
        dimension_column="mat_term_d_rn_description",
        dimension_values=["15TO91", "15-91 days"],
    )
    assert len(obs) == 2


# --- RbiSource HTTP behaviour (FakeSession) ----------------------------------


def test_fetch_series_uses_config_and_bearer_token():
    session = FakeSession(
        [_token_response(), FakeResponse(200, _gateway_payload("rbi_dbie_gsec_yield.json"))]
    )
    source = rbi.RbiSource(session=session)
    obs = source.fetch_series("in_gsec_10y")
    assert [o["value"] for o in obs] == [7.0231, 6.9902]
    token_call, data_call = session.calls
    assert token_call["url"].endswith("/security_generateSessionToken")
    assert data_call["url"].endswith("/dbie_getImpalaDQActionEnhanced")
    assert data_call["json"] == {"body": {"dsdCode": "YIELD_GOV_SEC_RN"}}
    assert data_call["headers"]["authorization"] == "Bearer guest-token"
    assert data_call["headers"]["channelkey"] == "key2"


def test_fetch_retries_429_then_succeeds(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    session = FakeSession(
        [
            _token_response(),
            FakeResponse(429, "slow down"),
            FakeResponse(200, _gateway_payload("rbi_dbie_tbill_yield.json")),
        ]
    )
    source = rbi.RbiSource(session=session)
    obs = source.fetch_series("in_gsec_91d")
    assert len(obs) == 2
    assert len(session.calls) == 3  # token + failed attempt + retry


def test_unconfigured_series_raises_clear_error():
    source = rbi.RbiSource(session=FakeSession([]))
    with pytest.raises(KeyError):
        source.fetch_series("nope")
    with pytest.raises(rbi.SourceError, match="no DBIE fetch parameters"):
        source.fetch_series("repo_rate")  # documented Key Rates gap


# --- sync (DuckDB, tmp data dir) ----------------------------------------------


def _rbi_session() -> FakeSession:
    return FakeSession(
        [
            _token_response(),
            FakeResponse(200, _gateway_payload("rbi_dbie_forex_reserves.json")),
            FakeResponse(200, _gateway_payload("rbi_dbie_gsec_yield.json")),
            FakeResponse(200, _gateway_payload("rbi_dbie_gsec_yield.json")),
            FakeResponse(200, _gateway_payload("rbi_dbie_tbill_yield.json")),
        ]
    )


def test_sync_writes_benchmarks_and_macro(db):
    summary = rbi.sync(db, source=rbi.RbiSource(session=_rbi_session()))
    assert summary["benchmark"] == {"in_gsec_10y": 2, "in_gsec_5y": 2, "in_gsec_91d": 2}
    assert summary["macro"] == {"forex_reserves": 2}
    # policy-rate series have no fetchable DBIE params yet -> skipped, logged
    assert set(summary["skipped"]) == {"repo_rate", "reverse_repo_rate", "crr", "rbi_repo"}

    rows = db.execute(
        "SELECT date, value FROM benchmark_observations WHERE series_key = 'in_gsec_10y'"
        " ORDER BY date"
    ).fetchall()
    assert [(str(r[0]), r[1]) for r in rows] == [("2026-07-01", 7.0231), ("2026-08-01", 6.9902)]

    # forex: weekly USD-million values scaled into USD bn; both weeks land in
    # period 2026-09, so the idempotent upsert keeps the latest observation.
    macro = db.execute(
        "SELECT period, value FROM macro_observations WHERE series_key = 'forex_reserves'"
    ).fetchall()
    assert macro == [("2026-09", 642.5189)]


def test_sync_is_idempotent(db):
    rbi.sync(db, source=rbi.RbiSource(session=_rbi_session()))
    rbi.sync(db, source=rbi.RbiSource(session=_rbi_session()))
    n = db.execute("SELECT COUNT(*) FROM benchmark_observations").fetchone()[0]
    assert n == 6


def test_sync_records_ingestion_audit_row(db):
    rbi.sync(db, source=rbi.RbiSource(session=_rbi_session()))
    row = db.execute(
        "SELECT status, rows_written, error FROM ingestion_runs WHERE job = ?",
        (rbi.JOB,),
    ).fetchone()
    assert row is not None
    assert row[0] == "partial"  # policy-rate series partial, not failed
    assert row[1] == 8
    assert "repo_rate" in row[2]
