"""P4-C: GET /api/health/data (data-quality status endpoint).

Uses the FastAPI TestClient against a throwaway BAZZAR_DATA_DIR; rows are
seeded straight into the data_quality audit table.
"""

from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from backend.db import get_connection


@pytest.fixture()
def api(tmp_path, monkeypatch):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    from backend.server import app

    with TestClient(app) as client:
        yield client


def _seed(con, severity, *, created_at=None, check="macro_freshness", target="cpi_inflation"):
    con.execute(
        "INSERT INTO data_quality (check_name, target, period, severity, message, created_at)"
        " VALUES (?, ?, '2026-09', ?, 'seeded row', ?)",
        (
            check,
            target,
            severity,
            created_at or dt.datetime.now(dt.UTC).replace(tzinfo=None),
        ),
    )


def _status(api):
    res = api.get("/api/health/data")
    assert res.status_code == 200
    return res.json()


def test_empty_table_is_green(api):
    body = _status(api)
    assert set(body) == {"status", "checks", "summary", "asOf"}
    assert body["status"] == "green"
    assert body["checks"] == []
    assert body["summary"] == {"info": 0, "warn": 0, "fail": 0}
    assert body["asOf"]  # utc iso timestamp present


def test_seeded_warn_is_amber(api):
    with get_connection() as con:
        _seed(con, "warn")
    body = _status(api)
    assert body["status"] == "amber"
    assert body["summary"] == {"info": 0, "warn": 1, "fail": 0}
    assert body["checks"][0]["severity"] == "warn"
    assert set(body["checks"][0]) == {
        "check_name",
        "target",
        "period",
        "severity",
        "message",
        "details",
        "created_at",
    }


def test_recent_fail_is_red(api):
    with get_connection() as con:
        _seed(con, "fail")
    body = _status(api)
    assert body["status"] == "red"
    assert body["summary"]["fail"] == 1


def test_old_fail_is_not_red(api):
    old = dt.datetime.now(dt.UTC).replace(tzinfo=None) - dt.timedelta(hours=72)
    with get_connection() as con:
        _seed(con, "fail", created_at=old)
    body = _status(api)
    assert body["status"] != "red"
    assert body["summary"]["fail"] == 1  # still counted in the summary


def test_resolved_fail_uses_latest_row(api):
    with get_connection() as con:
        _seed(con, "fail", check="kite_vs_bhavcopy", target="ALPHA")
        _seed(con, "info", check="kite_vs_bhavcopy", target="ALPHA")  # newer row wins
    body = _status(api)
    assert body["status"] == "green"
    assert len(body["checks"]) == 1  # latest row per (check_name, target)
    assert body["checks"][0]["severity"] == "info"
