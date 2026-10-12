"""P4-C: reconciliation & data-quality checks (backend.reconcile).

Fully offline: the bhavcopy side is a fake provider; macro/benchmark rows
are seeded through the validated upsert helpers.
"""

from __future__ import annotations

import datetime as dt

import pytest

from backend import reconcile
from backend.benchmarks import upsert_benchmark_observation
from backend.db import get_connection, initialize_database
from backend.macro import upsert_observation


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    initialize_database()
    con = get_connection()
    yield con
    con.close()


class FakeBhavcopyProvider:
    """Test double for NseBhavcopyProvider.fetch_day (no network)."""

    name = "fake_bhavcopy"

    def __init__(self, rows=None, error: Exception | None = None):
        self.rows = rows or []
        self.error = error
        self.calls: list[dt.date] = []

    def fetch_day(self, day):
        self.calls.append(day)
        if self.error:
            raise self.error
        return list(self.rows)


def _seed_bar(con, symbol="ALPHA", day=None, close=100.0):
    day = day or dt.date.today()
    con.execute(
        "INSERT INTO daily_ohlcv (symbol, exchange, date, open, high, low, close, volume)"
        " VALUES (?, 'NSE', ?, ?, ?, ?, ?, 1)"
        " ON CONFLICT (symbol, exchange, date) DO UPDATE SET close = excluded.close",
        (symbol, str(day), close, close, close, close),
    )
    return day


def _bhav_row(symbol, close, day=None):
    day = day or dt.date.today()
    return {
        "symbol": symbol,
        "date": day.isoformat(),
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": 1,
    }


def _monthly_period(months_back: int) -> str:
    today = dt.date.today()
    total = today.year * 12 + (today.month - 1) - months_back
    return f"{total // 12}-{total % 12 + 1:02d}"


def _quarterly_period(quarters_back: int) -> str:
    today = dt.date.today()
    total = today.year * 4 + (today.month - 1) // 3 - quarters_back
    return f"{total // 4}-Q{total % 4 + 1}"


def _rows(con, check_name=None):
    sql = "SELECT check_name, target, severity, message FROM data_quality"
    if check_name:
        sql += f" WHERE check_name = '{check_name}'"
    return con.execute(sql + " ORDER BY id").fetchall()


# --- check_kite_vs_bhavcopy ---------------------------------------------------


def test_kite_vs_bhavcopy_match_records_no_warn(db):
    day = _seed_bar(db, close=100.0)
    provider = FakeBhavcopyProvider([_bhav_row("ALPHA", 100.2, day)])  # 0.2% diff
    rows = reconcile.check_kite_vs_bhavcopy(db, provider=provider)
    assert provider.calls == [day]
    assert [r["severity"] for r in rows] == ["info"]
    assert rows[0]["details"]["stored_close"] == 100.0
    assert rows[0]["details"]["bhavcopy_close"] == 100.2


def test_kite_vs_bhavcopy_mismatch_warns(db):
    day = _seed_bar(db, close=100.0)
    provider = FakeBhavcopyProvider([_bhav_row("ALPHA", 100.7, day)])  # 0.7% > 0.5%
    rows = reconcile.check_kite_vs_bhavcopy(db, provider=provider)
    assert [r["severity"] for r in rows] == ["warn"]
    assert "differs from bhavcopy" in rows[0]["message"]


def test_kite_vs_bhavcopy_large_mismatch_fails(db):
    day = _seed_bar(db, close=100.0)
    provider = FakeBhavcopyProvider([_bhav_row("ALPHA", 103.0, day)])  # 3% > 2x tol
    rows = reconcile.check_kite_vs_bhavcopy(db, provider=provider)
    assert [r["severity"] for r in rows] == ["fail"]


def test_kite_vs_bhavcopy_missing_side_is_info(db):
    day = _seed_bar(db, close=100.0)
    # symbol absent from the bhavcopy -> "no data to compare", never invented
    rows = reconcile.check_kite_vs_bhavcopy(db, provider=FakeBhavcopyProvider([]))
    assert [r["severity"] for r in rows] == ["info"]
    assert "no data to compare" in rows[0]["message"]
    assert "no bhavcopy rows" in rows[0]["message"]

    provider = FakeBhavcopyProvider([_bhav_row("OTHER", 50.0, day)])
    rows = reconcile.check_kite_vs_bhavcopy(db, provider=provider)
    assert [r["severity"] for r in rows] == ["info"]
    assert "no data to compare" in rows[0]["message"]


def test_kite_vs_bhavcopy_no_bars_is_info(db):
    rows = reconcile.check_kite_vs_bhavcopy(db, provider=FakeBhavcopyProvider())
    assert [r["severity"] for r in rows] == ["info"]
    assert "no NSE bars stored" in rows[0]["message"]


def test_kite_vs_bhavcopy_provider_error_is_info(db):
    _seed_bar(db, close=100.0)
    provider = FakeBhavcopyProvider(error=ConnectionError("offline"))
    rows = reconcile.check_kite_vs_bhavcopy(db, provider=provider)
    assert [r["severity"] for r in rows] == ["info"]
    assert "unavailable" in rows[0]["message"]


def test_kite_vs_bhavcopy_stale_bars_skipped(db):
    old = dt.date.today() - dt.timedelta(days=30)
    _seed_bar(db, day=old, close=100.0)
    provider = FakeBhavcopyProvider([_bhav_row("ALPHA", 100.0, old)])
    rows = reconcile.check_kite_vs_bhavcopy(db, provider=provider)
    assert [r["severity"] for r in rows] == ["info"]
    assert "nothing current to reconcile" in rows[0]["message"]
    assert provider.calls == []  # no fetch for stale stores


# --- check_macro_freshness ------------------------------------------------------


def test_macro_freshness_fresh_monthly(db):
    upsert_observation(db, "cpi_inflation", _monthly_period(1), 5.0)
    rows = reconcile.check_macro_freshness(db)
    row = next(r for r in rows if r["target"] == "cpi_inflation")
    assert row["severity"] == "info"
    assert "fresh" in row["message"]


def test_macro_freshness_stale_monthly_warns(db):
    upsert_observation(db, "cpi_inflation", _monthly_period(3), 5.0)  # lag 3 > tol 2
    rows = reconcile.check_macro_freshness(db)
    row = next(r for r in rows if r["target"] == "cpi_inflation")
    assert row["severity"] == "warn"
    assert "stale" in row["message"]


def test_macro_freshness_very_stale_monthly_fails(db):
    upsert_observation(db, "cpi_inflation", _monthly_period(9), 5.0)  # lag 9 > 2x tol
    rows = reconcile.check_macro_freshness(db)
    row = next(r for r in rows if r["target"] == "cpi_inflation")
    assert row["severity"] == "fail"
    assert "very stale" in row["message"]


def test_macro_freshness_quarterly(db):
    upsert_observation(db, "gdp_growth", _quarterly_period(1), 7.0)
    rows = reconcile.check_macro_freshness(db)
    row = next(r for r in rows if r["target"] == "gdp_growth")
    assert row["severity"] == "info"
    assert "fresh" in row["message"]


def test_macro_freshness_never_synced_is_info(db):
    rows = reconcile.check_macro_freshness(db)  # empty macro_observations
    assert rows  # one row per registered series
    assert {r["severity"] for r in rows} == {"info"}
    assert all("never synced" in r["message"] for r in rows)


def test_macro_freshness_event_driven_not_checked(db):
    upsert_observation(db, "repo_rate", "2020-01", 4.0)  # ancient but event-driven
    rows = reconcile.check_macro_freshness(db)
    row = next(r for r in rows if r["target"] == "repo_rate")
    assert row["severity"] == "info"
    assert "no cadence expectation" in row["message"]


# --- check_benchmark_freshness --------------------------------------------------


def test_benchmark_freshness_fresh_daily(db):
    upsert_benchmark_observation(db, "fii_net", dt.date.today().isoformat(), 100.0)
    rows = reconcile.check_benchmark_freshness(db)
    row = next(r for r in rows if r["target"] == "fii_net")
    assert row["severity"] == "info"
    assert "fresh" in row["message"]


def test_benchmark_freshness_stale_daily_warns(db):
    old = (dt.date.today() - dt.timedelta(days=10)).isoformat()  # > 7d, <= 14d
    upsert_benchmark_observation(db, "fii_net", old, 100.0)
    rows = reconcile.check_benchmark_freshness(db)
    row = next(r for r in rows if r["target"] == "fii_net")
    assert row["severity"] == "warn"


def test_benchmark_freshness_very_stale_daily_fails(db):
    old = (dt.date.today() - dt.timedelta(days=30)).isoformat()  # > 2x 7d
    upsert_benchmark_observation(db, "fii_net", old, 100.0)
    rows = reconcile.check_benchmark_freshness(db)
    row = next(r for r in rows if r["target"] == "fii_net")
    assert row["severity"] == "fail"


def test_benchmark_freshness_never_synced_and_uncadenced(db):
    rows = reconcile.check_benchmark_freshness(db)  # empty benchmark_observations
    by_target = {r["target"]: r for r in rows}
    assert by_target["in_gsec_10y"]["severity"] == "info"
    assert "never synced" in by_target["in_gsec_10y"]["message"]
    assert by_target["sgb_price"]["severity"] == "info"
    assert "no freshness expectation" in by_target["sgb_price"]["message"]


# --- run_all + CLI ---------------------------------------------------------------


def test_run_all_empty_db_is_green_and_audited(db):
    summary = reconcile.run_all(db, provider=FakeBhavcopyProvider())
    assert summary["checks_run"] == 3
    assert summary["fail"] == 0
    assert summary["warn"] == 0
    assert summary["info"] > 0
    assert summary["status"] == "green"

    run = db.execute(
        "SELECT job, status, rows_written FROM ingestion_runs WHERE job = 'reconcile'"
    ).fetchone()
    assert run is not None
    assert run[1] == "success"
    assert run[2] == summary["info"]  # every recorded row counted
    stored = db.execute("SELECT COUNT(*) FROM data_quality").fetchone()[0]
    assert stored == summary["info"]


def test_run_all_fail_marks_run_partial(db):
    upsert_observation(db, "cpi_inflation", _monthly_period(9), 5.0)  # very stale -> fail
    summary = reconcile.run_all(db, provider=FakeBhavcopyProvider())
    assert summary["fail"] >= 1
    assert summary["status"] == "red"
    status, error = db.execute(
        "SELECT status, error FROM ingestion_runs WHERE job = 'reconcile'"
    ).fetchone()
    assert status == "partial"
    assert "fail-severity" in error


def test_run_all_crashing_check_becomes_fail_row(db, monkeypatch):
    def boom(con):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(reconcile, "check_macro_freshness", boom)
    summary = reconcile.run_all(db, provider=FakeBhavcopyProvider())
    assert summary["fail"] >= 1
    crash = [r for r in summary["rows"] if "check crashed" in r["message"]]
    assert len(crash) == 1
    assert crash[0]["check_name"] == "macro_freshness"


def test_cli_exit_codes(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    assert reconcile.main([]) == 0  # empty db -> all info -> green
    out = capsys.readouterr().out
    assert "reconcile: 3 checks run" in out
    assert "status=green" in out

    con = get_connection()
    try:
        upsert_observation(con, "cpi_inflation", _monthly_period(9), 5.0)
    finally:
        con.close()
    assert reconcile.main([]) == 1  # fail-severity finding -> exit 1
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert "status=red" in out


def test_period_lag_units():
    today = dt.date(2026, 10, 12)
    assert reconcile._period_lag("2026-09", "monthly", today) == 1
    assert reconcile._period_lag("2026-Q2", "quarterly", today) == 2
    assert reconcile._period_lag("2026-10-01", "weekly", today) == 11
    assert reconcile._period_lag("not-a-period", "monthly", today) is None
