"""P3: fetcher provider-selection tests — --provider flag, provider factory
injection, per-symbol failure → partial run, auth failure → abort.
"""

from __future__ import annotations

import pytest

from backend import fetch_daily
from backend.db import get_connection, initialize_database
from backend.fetch_daily import JOB, get_checkpoint
from backend.providers.base import ProviderAuthRequired, ProviderError

TRADING_DAY = "2025-01-06"  # Monday — in the seeded trading calendar


class FakeProvider:
    name = "fake"

    def __init__(self, bars_by_symbol=None, failures=None):
        self.bars_by_symbol = bars_by_symbol or {}
        self.failures = failures or {}
        self.calls: list[tuple[str, str, str, str]] = []

    def history_daily(self, symbol, exchange, start, end):
        self.calls.append((symbol, exchange, start, end))
        if symbol in self.failures:
            raise self.failures[symbol]
        return list(self.bars_by_symbol.get(symbol, []))


def _bar(day=TRADING_DAY, close=100.0):
    return {"date": day, "open": close, "high": close, "low": close, "close": close, "volume": 1}


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    initialize_database()
    con = get_connection()
    con.executemany(
        "INSERT INTO securities (symbol, name, exchange, instrument_type, isin, active)"
        " VALUES (?, ?, ?, 'EQ', NULL, TRUE)",
        [("ALPHA", "Alpha Ltd", "NSE"), ("BRAVO", "Bravo Ltd", "NSE")],
    )
    con.close()

    def _use(provider):
        monkeypatch.setattr(fetch_daily, "get_provider", lambda name=None, *, con=None: provider)

    yield _use


def _run_status(con):
    return con.execute(
        "SELECT status, error FROM ingestion_runs WHERE job = ? ORDER BY run_id DESC LIMIT 1",
        (JOB,),
    ).fetchone()


def test_run_uses_injected_provider_and_checkpoints(db):
    provider = FakeProvider({"ALPHA": [_bar()], "BRAVO": [_bar()]})
    db(provider)
    assert fetch_daily.run(TRADING_DAY, TRADING_DAY, provider_name="kite") == 0
    assert [c[0] for c in provider.calls] == ["ALPHA", "BRAVO"]

    con = get_connection()
    try:
        count = con.execute("SELECT COUNT(*) FROM daily_ohlcv").fetchone()[0]
        assert count == 2
        assert get_checkpoint(con, JOB) == "BRAVO"
        assert _run_status(con) == ("success", None)
    finally:
        con.close()


def test_auth_failure_aborts_run_and_keeps_checkpoint(db):
    provider = FakeProvider(
        bars_by_symbol={"BRAVO": [_bar()]},
        failures={"ALPHA": ProviderAuthRequired("token expired")},
    )
    db(provider)
    with pytest.raises(ProviderAuthRequired):
        fetch_daily.run(TRADING_DAY, TRADING_DAY)

    con = get_connection()
    try:
        assert get_checkpoint(con, JOB) is None  # ALPHA never checkpointed
        assert con.execute("SELECT COUNT(*) FROM daily_ohlcv").fetchone()[0] == 0
        status, _ = _run_status(con)
        assert status == "failed"
    finally:
        con.close()


def test_per_symbol_failure_skips_and_marks_run_partial(db):
    provider = FakeProvider(
        bars_by_symbol={"BRAVO": [_bar()]},
        failures={"ALPHA": ProviderError("no instrument_token for NSE:ALPHA")},
    )
    db(provider)
    assert fetch_daily.run(TRADING_DAY, TRADING_DAY) == 0  # run completes

    con = get_connection()
    try:
        symbols = [r[0] for r in con.execute("SELECT symbol FROM daily_ohlcv").fetchall()]
        assert symbols == ["BRAVO"]  # ALPHA skipped
        assert get_checkpoint(con, JOB) == "BRAVO"  # checkpoint advances past failure
        status, error = _run_status(con)
        assert status == "partial"
        assert "ALPHA" in error
    finally:
        con.close()


def test_cli_provider_flag():
    parser = fetch_daily.build_parser()
    args = parser.parse_args(["--provider", "kite"])
    assert args.provider == "kite"
    args = parser.parse_args([])
    assert args.provider is None  # falls back to MARKET_DATA_PROVIDER setting
