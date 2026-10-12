"""P3: instrument-master sync tests — Kite dump → securities table upserts,
symbol normalisation, index segment mapping, deactivation, audit trail.
"""

from __future__ import annotations

import pytest

from backend.db import get_connection, initialize_database
from backend.providers.base import Instrument
from backend.sync_instruments import JOB, sync_instruments, target_exchange


class FakeInstrumentsProvider:
    name = "fake"

    def __init__(self, rows_by_exchange: dict[str, list[Instrument]]):
        self.rows_by_exchange = rows_by_exchange

    def instruments(self, exchange=None):
        return list(self.rows_by_exchange.get(exchange, []))


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    initialize_database()
    con = get_connection()
    yield con
    con.close()


@pytest.fixture()
def provider():
    return FakeInstrumentsProvider(
        {
            "NSE": [
                Instrument(
                    symbol="infy",  # lowercase: must be normalised to upper
                    exchange="NSE",
                    name="Infosys Ltd",
                    instrument_type="EQ",
                    isin="INE009A01021",
                    instrument_token=408065,
                    lot_size=1,
                    tick_size=0.05,
                    segment="NSE",
                ),
                Instrument(
                    symbol="NIFTY 50",
                    exchange="NSE",
                    name="",
                    instrument_type="INDEX",
                    isin=None,
                    instrument_token=256265,
                    lot_size=None,
                    tick_size=None,
                    segment="INDICES",
                ),
                Instrument(
                    symbol="INFY25JANFUT",
                    exchange="NSE",
                    name="",
                    instrument_type="FUT",
                    instrument_token=111,
                    segment="NFO-FUT",
                ),
            ],
            "BSE": [],
        }
    )


def test_target_exchange_maps_index_segment():
    assert target_exchange("NSE", "INDICES") == "NSE_INDEX"
    assert target_exchange("BSE", "INDICES") == "BSE_INDEX"
    assert target_exchange("NSE", "NSE") == "NSE"


def test_sync_upserts_equity_and_index_rows(db, provider):
    stats = sync_instruments(db, provider)
    assert stats == {"written": 2, "skipped": 1, "deactivated": 0}  # FUT skipped

    row = db.execute(
        "SELECT symbol, name, exchange, instrument_type, isin, active,"
        " instrument_token, lot_size, tick_size FROM securities WHERE symbol = 'INFY'"
    ).fetchone()
    assert row == ("INFY", "Infosys Ltd", "NSE", "EQ", "INE009A01021", True, 408065, 1, 0.05)

    nifty = db.execute(
        "SELECT symbol, exchange, instrument_type, instrument_token FROM securities"
        " WHERE symbol = 'NIFTY 50'"
    ).fetchone()
    assert nifty == ("NIFTY 50", "NSE_INDEX", "INDEX", 256265)


def test_sync_is_idempotent(db, provider):
    sync_instruments(db, provider)
    sync_instruments(db, provider)
    count = db.execute("SELECT COUNT(*) FROM securities").fetchone()[0]
    assert count == 2


def test_vanished_listings_are_deactivated_not_deleted(db, provider):
    sync_instruments(db, provider)
    # Second dump: INFY vanished from the master, NIFTY 50 remains.
    shrunk = FakeInstrumentsProvider(
        {
            "NSE": [inst for inst in provider.rows_by_exchange["NSE"] if inst.symbol == "NIFTY 50"],
            "BSE": [],
        }
    )
    stats = sync_instruments(db, shrunk)
    assert stats["deactivated"] == 1
    rows = db.execute("SELECT symbol, active FROM securities ORDER BY symbol").fetchall()
    assert rows == [("INFY", False), ("NIFTY 50", True)]  # INFY kept, inactive


def test_empty_dump_never_deactivates(db, provider):
    """Guard rail: an empty/garbled instrument dump must not wipe the table."""
    sync_instruments(db, provider)
    empty = FakeInstrumentsProvider({"NSE": [], "BSE": []})
    stats = sync_instruments(db, empty)
    assert stats["deactivated"] == 0
    rows = db.execute("SELECT symbol, active FROM securities ORDER BY symbol").fetchall()
    assert rows == [("INFY", True), ("NIFTY 50", True)]


def test_sync_records_ingestion_run(db, provider):
    sync_instruments(db, provider)
    row = db.execute(
        "SELECT job, rows_written, rows_rejected, status FROM ingestion_runs"
        " ORDER BY run_id DESC LIMIT 1"
    ).fetchone()
    assert row == (JOB, 2, 1, "success")
