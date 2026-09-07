"""Exchange trading calendar.

The ``trading_calendar`` table (migration 0002) is seeded from
``backend/data/nse_calendar.csv`` — a static, reviewable artifact covering
2025-01-01 .. 2026-12-31. Holiday dates come from NSE Capital Market Segment
circulars 170/2024 (calendar 2025) and 172/2025 + 03/2026 (calendar 2026);
special sessions (Union Budget Saturday 2025-02-01, Muhurat trading
2025-10-21 and 2026-11-08) are marked as trading days because official daily
bars exist for those sessions.

Semantics used by validators:
  * row present, is_trading_day = false  -> known non-trading day (reject)
  * row present, is_trading_day = true   -> known trading day (accept)
  * no row (outside seeded coverage)     -> UNKNOWN: never reject on
    calendar grounds (historical data predates the seeded window)

Refresh: regenerate the CSV annually when NSE publishes the next calendar
(see backend/data/README note in ARCHITECTURE.md), then restart — seeding is
an idempotent upsert.
"""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

import duckdb

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_SEED_CSV = PACKAGE_DIR / "data" / "nse_calendar.csv"
DEFAULT_EXCHANGE = "NSE"


def seed_trading_calendar(
    con: duckdb.DuckDBPyConnection,
    csv_path: str | Path | None = None,
    exchange: str = DEFAULT_EXCHANGE,
) -> int:
    """Idempotently upsert calendar rows from the seed CSV. Returns row count."""
    path = Path(csv_path) if csv_path else DEFAULT_SEED_CSV
    rows: list[tuple[str, str, bool, str | None]] = []
    with open(path, newline="", encoding="utf-8") as fh:
        for record in csv.DictReader(fh):
            name = (record.get("holiday_name") or "").strip() or None
            rows.append(
                (
                    exchange,
                    record["date"].strip(),
                    record["is_trading_day"].strip().lower() in ("1", "true", "yes"),
                    name,
                )
            )
    con.executemany(
        "INSERT INTO trading_calendar (exchange, date, is_trading_day, holiday_name)"
        " VALUES (?, ?, ?, ?)"
        " ON CONFLICT (exchange, date) DO UPDATE SET"
        " is_trading_day = excluded.is_trading_day,"
        " holiday_name = excluded.holiday_name",
        rows,
    )
    return len(rows)


def is_trading_day(
    con: duckdb.DuckDBPyConnection,
    day: dt.date | str,
    exchange: str = DEFAULT_EXCHANGE,
) -> bool | None:
    """True/False if the date is inside seeded coverage, None if unknown."""
    row = con.execute(
        "SELECT is_trading_day FROM trading_calendar WHERE exchange = ? AND date = ?",
        (exchange, str(day)),
    ).fetchone()
    return bool(row[0]) if row else None


def holiday_name(
    con: duckdb.DuckDBPyConnection,
    day: dt.date | str,
    exchange: str = DEFAULT_EXCHANGE,
) -> str | None:
    row = con.execute(
        "SELECT holiday_name FROM trading_calendar WHERE exchange = ? AND date = ?",
        (exchange, str(day)),
    ).fetchone()
    return row[0] if row else None


def coverage(
    con: duckdb.DuckDBPyConnection,
    exchange: str = DEFAULT_EXCHANGE,
) -> tuple[dt.date, dt.date] | None:
    """(min_date, max_date) of the seeded calendar window, or None if empty."""
    row = con.execute(
        "SELECT MIN(date), MAX(date) FROM trading_calendar WHERE exchange = ?",
        (exchange,),
    ).fetchone()
    if not row or row[0] is None:
        return None
    return row[0], row[1]


def next_trading_day(
    con: duckdb.DuckDBPyConnection,
    day: dt.date | str,
    exchange: str = DEFAULT_EXCHANGE,
) -> dt.date | None:
    row = con.execute(
        "SELECT MIN(date) FROM trading_calendar WHERE exchange = ? AND date > ? AND is_trading_day",
        (exchange, str(day)),
    ).fetchone()
    return row[0] if row and row[0] is not None else None


def previous_trading_day(
    con: duckdb.DuckDBPyConnection,
    day: dt.date | str,
    exchange: str = DEFAULT_EXCHANGE,
) -> dt.date | None:
    row = con.execute(
        "SELECT MAX(date) FROM trading_calendar WHERE exchange = ? AND date < ? AND is_trading_day",
        (exchange, str(day)),
    ).fetchone()
    return row[0] if row and row[0] is not None else None
