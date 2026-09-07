"""P2: trading calendar + ingestion audit tests."""

from __future__ import annotations

import datetime as dt

import pytest

from backend.calendar import (
    coverage,
    holiday_name,
    is_trading_day,
    next_trading_day,
    previous_trading_day,
)
from backend.db import get_connection, initialize_database
from backend.ingestion import data_freshness, ingestion_run, latest_runs


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    summary = initialize_database()
    con = get_connection()
    yield con, summary
    con.close()


# --- calendar ---------------------------------------------------------------


def test_calendar_seeded_full_coverage(db):
    con, summary = db
    assert summary["trading_calendar"] == 730  # 2025 + 2026, every day
    assert coverage(con) == (dt.date(2025, 1, 1), dt.date(2026, 12, 31))


@pytest.mark.parametrize(
    "day, expected",
    [
        ("2025-01-06", True),  # plain Monday
        ("2025-01-04", False),  # Saturday
        ("2025-12-25", False),  # Christmas
        ("2026-01-15", False),  # municipal election holiday (circular 03/2026)
        ("2025-02-01", True),  # Union Budget special Saturday session
        ("2025-10-21", True),  # Muhurat trading (listed holiday, real bars)
        ("2026-11-08", True),  # Muhurat trading (special Sunday session)
        ("2024-06-03", None),  # outside coverage -> unknown
    ],
)
def test_is_trading_day(db, day, expected):
    con, _ = db
    assert is_trading_day(con, day) is expected


def test_holiday_name(db):
    con, _ = db
    assert holiday_name(con, "2025-12-25") == "Christmas"
    assert holiday_name(con, "2025-01-06") in (None, "")


def test_next_and_previous_trading_day(db):
    con, _ = db
    # Friday 2025-01-03 -> next trading day is Monday 2025-01-06.
    assert next_trading_day(con, "2025-01-03") == dt.date(2025, 1, 6)
    assert previous_trading_day(con, "2025-01-06") == dt.date(2025, 1, 3)
    # Christmas 2025: next trading day is Friday 2025-12-26.
    assert next_trading_day(con, "2025-12-25") == dt.date(2025, 12, 26)


# --- ingestion audit ---------------------------------------------------------


def test_ingestion_run_records_success(db):
    con, _ = db
    with ingestion_run(con, "daily_equity") as run:
        run.rows_written = 42
        run.rows_rejected = 1
    row = con.execute(
        "SELECT job, rows_written, rows_rejected, status, error, finished_at FROM ingestion_runs"
    ).fetchone()
    assert row[:5] == ("daily_equity", 42, 1, "success", None)
    assert row[5] is not None


def test_ingestion_run_records_failure_and_reraises(db):
    con, _ = db
    with pytest.raises(RuntimeError, match="boom"), ingestion_run(con, "daily_equity"):
        raise RuntimeError("boom")
    row = con.execute("SELECT status, error FROM ingestion_runs").fetchone()
    assert row[0] == "failed" and "boom" in row[1]


def test_data_freshness_reports_asof(db):
    con, _ = db
    with ingestion_run(con, "daily_equity") as run:
        con.execute(
            "INSERT INTO daily_ohlcv (symbol, exchange, date, open, high, low, close,"
            " volume) VALUES ('AAA', 'NSE', '2025-01-06', 1, 1, 1, 1, 1)"
        )
        run.rows_written = 1
    report = data_freshness(con)
    assert len(report) == 1
    entry = report[0]
    assert entry["job"] == "daily_equity"
    assert entry["last_status"] == "success"
    assert entry["data_as_of"] == "2025-01-06"


def test_latest_runs_newest_first(db):
    con, _ = db
    for _ in range(3):
        with ingestion_run(con, "daily_indices"):
            pass
    runs = latest_runs(con, limit=10)
    assert len(runs) == 3
    ids = [r["run_id"] for r in runs]
    assert ids == sorted(ids, reverse=True)
