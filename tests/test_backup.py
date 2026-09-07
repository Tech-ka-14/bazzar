"""P2: backup/restore round-trip and retention tests."""

from __future__ import annotations

import datetime as dt

import pytest

from backend.backup import (
    apply_retention,
    backups_root,
    create_backup,
    restore_backup,
    table_counts,
)
from backend.db import get_connection, initialize_database
from backend.validation import upsert_daily_ohlcv


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    initialize_database()
    con = get_connection()
    yield con, tmp_path
    con.close()


def _seed_some_bars(con):
    bars = [
        {"date": d, "open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 10}
        for d in ("2025-01-06", "2025-01-07", "2025-01-08")
    ]
    upsert_daily_ohlcv(con, job="daily_equity", symbol="AAA", exchange="NSE", bars=bars)


def test_backup_restore_round_trip_identical_counts(db):
    con, tmp_path = db
    _seed_some_bars(con)

    snapshot = create_backup(con)
    assert (snapshot / "schema.sql").exists()

    live_counts = table_counts(con)
    restored_db = tmp_path / "restored.duckdb"
    restored_counts = restore_backup(snapshot, restored_db)
    assert restored_counts == live_counts
    assert restored_counts["daily_ohlcv"] == 3
    assert restored_counts["trading_calendar"] == 730


def test_restore_refuses_existing_target(db, tmp_path):
    con, data_dir = db
    snapshot = create_backup(con)
    existing = data_dir / "exists.duckdb"
    existing.touch()
    with pytest.raises(FileExistsError):
        restore_backup(snapshot, existing)


def test_restore_rejects_non_snapshot(db, tmp_path):
    with pytest.raises(FileNotFoundError):
        restore_backup(tmp_path, tmp_path / "x.duckdb")


def test_retention_keeps_daily_plus_monthly(tmp_path):
    root = tmp_path / "backups"
    # 80 consecutive daily snapshots spanning Jan/Feb/Mar 2026.
    base = dt.datetime(2026, 1, 1, 9, 0, 0)
    for i in range(80):
        day = base + dt.timedelta(days=i)
        (root / day.strftime("%Y%m%d_%H%M%S")).mkdir(parents=True)

    apply_retention(root)
    remaining = sorted(p.name for p in root.iterdir())

    # The newest 14 are always kept (days 66..79 -> 2026-03-08 .. 2026-03-21).
    expected_daily = [
        (base + dt.timedelta(days=i)).strftime("%Y%m%d_%H%M%S") for i in range(66, 80)
    ]
    for name in expected_daily:
        assert name in remaining
    # Plus the newest snapshot of each older month: 2026-01-31 and 2026-02-28.
    assert "20260131_090000" in remaining
    assert "20260228_090000" in remaining
    # 14 daily + 2 monthly, nothing else.
    assert len(remaining) == 16


def test_backups_root_under_data_dir(db):
    _, data_dir = db
    assert backups_root().parent == data_dir
