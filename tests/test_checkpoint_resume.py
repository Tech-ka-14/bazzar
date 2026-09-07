"""P2: checkpoint resume tests — an interrupted fetch resumes at the symbol
after the recorded checkpoint, in strict alphabetical order."""

from __future__ import annotations

import pytest

from backend.db import get_connection, initialize_database
from backend.fetch_daily import JOB, get_checkpoint, pending_symbols, set_checkpoint


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    initialize_database()
    con = get_connection()
    con.executemany(
        "INSERT INTO securities (symbol, name, exchange, instrument_type, isin, active)"
        " VALUES (?, ?, ?, 'EQ', NULL, TRUE)",
        [
            ("ALPHA", "Alpha Ltd", "NSE"),
            ("BRAVO", "Bravo Ltd", "NSE"),
            ("CHARLIE", "Charlie Ltd", "NSE"),
            ("DELTA", "Delta Ltd", "NSE"),
            ("INACTIVE", "Inactive Ltd", "NSE"),
        ],
    )
    con.execute("UPDATE securities SET active = FALSE WHERE symbol = 'INACTIVE'")
    yield con
    con.close()


def test_pending_symbols_alphabetical_without_checkpoint(db):
    symbols = [s for s, _ in pending_symbols(db, JOB)]
    assert symbols == ["ALPHA", "BRAVO", "CHARLIE", "DELTA"]  # INACTIVE excluded


def test_interrupted_run_resumes_after_checkpoint(db):
    # Simulate a run that completed ALPHA and BRAVO, then died.
    set_checkpoint(db, JOB, "BRAVO")
    assert get_checkpoint(db, JOB) == "BRAVO"
    symbols = [s for s, _ in pending_symbols(db, JOB)]
    assert symbols == ["CHARLIE", "DELTA"]


def test_completed_run_has_nothing_pending(db):
    set_checkpoint(db, JOB, "DELTA")
    assert pending_symbols(db, JOB) == []


def test_checkpoint_upsert_overwrites(db):
    set_checkpoint(db, JOB, "ALPHA")
    set_checkpoint(db, JOB, "CHARLIE")
    assert get_checkpoint(db, JOB) == "CHARLIE"
    rows = db.execute("SELECT COUNT(*) FROM fetch_checkpoint WHERE job = ?", (JOB,)).fetchone()
    assert rows[0] == 1
