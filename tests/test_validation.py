"""P2: write-path validation tests — invalid bars are rejected & quarantined,
never silently dropped, never crashing the run."""

from __future__ import annotations

import datetime as dt

import pytest

from backend.db import get_connection, initialize_database
from backend.validation import (
    Reject,
    quarantine_rejects,
    upsert_daily_ohlcv,
    upsert_index_daily,
    validate_bars,
)

# 2025-01-06 was a Monday and a normal trading day.
TRADING_DAY = "2025-01-06"
# 2025-01-04 was a Saturday (weekend, inside calendar coverage).
WEEKEND = "2025-01-04"
# 2025-12-25 was Christmas (holiday, inside coverage).
HOLIDAY = "2025-12-25"
# Far past, outside seeded calendar coverage (2025-01-01..2026-12-31).
OLD_DAY = "2010-06-15"  # a Tuesday


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    initialize_database()
    con = get_connection()
    yield con
    con.close()


def _bar(date: str = TRADING_DAY, **overrides) -> dict:
    bar = {
        "date": date,
        "open": 100.0,
        "high": 110.0,
        "low": 95.0,
        "close": 105.0,
        "volume": 1_000_000,
    }
    bar.update(overrides)
    return bar


def test_valid_bar_passes(db):
    valid, rejects = validate_bars([_bar()], symbol="AAA", exchange="NSE", con=db)
    assert len(valid) == 1 and rejects == []


@pytest.mark.parametrize(
    "override, reason_fragment",
    [
        ({"high": 90.0}, "high (90.0) < low (95.0)"),
        ({"open": 120.0}, "outside [low, high]"),
        ({"close": 94.0}, "outside [low, high]"),
        ({"volume": -5}, "negative volume"),
        ({"open": 0.0}, "non-positive price"),
        ({"close": None}, "missing field: close"),
        ({"date": "not-a-date"}, "unparseable date"),
    ],
)
def test_structural_rules_reject(db, override, reason_fragment):
    valid, rejects = validate_bars([_bar(**override)], symbol="AAA", exchange="NSE", con=db)
    assert valid == []
    assert len(rejects) == 1
    assert reason_fragment in rejects[0].reason


def test_future_date_rejected(db):
    future = (dt.date.today() + dt.timedelta(days=1)).isoformat()
    valid, rejects = validate_bars([_bar(date=future)], symbol="AAA", exchange="NSE", con=db)
    assert valid == [] and "future date" in rejects[0].reason


def test_weekend_and_holiday_rejected_inside_coverage(db):
    for day, name in ((WEEKEND, "Weekend"), (HOLIDAY, "Christmas")):
        valid, rejects = validate_bars([_bar(date=day)], symbol="AAA", exchange="NSE", con=db)
        assert valid == []
        assert "non-trading day" in rejects[0].reason
        assert name in rejects[0].reason


def test_unknown_calendar_date_allowed(db):
    # Outside the seeded coverage window the calendar check must not reject.
    valid, rejects = validate_bars([_bar(date=OLD_DAY)], symbol="AAA", exchange="NSE", con=db)
    assert len(valid) == 1 and rejects == []


def test_duplicate_dates_in_batch(db):
    valid, rejects = validate_bars([_bar(), _bar()], symbol="AAA", exchange="NSE", con=db)
    assert len(valid) == 1
    assert len(rejects) == 1 and "duplicate date" in rejects[0].reason


def test_rejects_are_quarantined_with_reason(db):
    n = quarantine_rejects(
        db,
        job="daily_equity",
        table_name="daily_ohlcv",
        rejects=[Reject(payload={"symbol": "AAA", "date": WEEKEND}, reason="non-trading day")],
    )
    assert n == 1
    row = db.execute("SELECT job, table_name, payload, reason FROM data_rejects").fetchone()
    assert row[0] == "daily_equity" and row[1] == "daily_ohlcv"
    assert "AAA" in row[2] and "non-trading day" in row[3]


def test_upsert_validates_writes_and_quarantines(db):
    bars = [_bar(), _bar(date=WEEKEND), _bar(date="2025-01-07")]
    written, rejected = upsert_daily_ohlcv(
        db, job="daily_equity", symbol="AAA", exchange="NSE", bars=bars
    )
    assert (written, rejected) == (2, 1)
    assert db.execute("SELECT COUNT(*) FROM daily_ohlcv").fetchone()[0] == 2
    assert db.execute("SELECT COUNT(*) FROM data_rejects").fetchone()[0] == 1


def test_upsert_is_idempotent(db):
    bars = [_bar(), _bar(date="2025-01-07")]
    upsert_daily_ohlcv(db, job="daily_equity", symbol="AAA", exchange="NSE", bars=bars)
    upsert_daily_ohlcv(db, job="daily_equity", symbol="AAA", exchange="NSE", bars=bars)
    assert db.execute("SELECT COUNT(*) FROM daily_ohlcv").fetchone()[0] == 2


def test_index_bars_volume_optional(db):
    bar = _bar()
    del bar["volume"]
    written, rejected = upsert_index_daily(
        db, job="daily_indices", symbol="NIFTY 50", exchange="NSE_INDEX", bars=[bar]
    )
    assert (written, rejected) == (1, 0)
    assert db.execute("SELECT COUNT(*) FROM index_daily").fetchone()[0] == 1
