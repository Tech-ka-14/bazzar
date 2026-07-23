"""Daily OHLC puller for the full index universe (index_master).

Same checkpoint discipline as fetch_daily (job="daily_indices"): symbols are
processed in alphabetical order (index_master.sort_order is assigned
alphabetically), and fetch_checkpoint records the last completed symbol so an
interrupted run resumes at the next one.

Also maintains the `index_snapshot` helper view, which computes per index:
latest daily OHLC (as of the most recent date in index_daily) plus the
52-week (year) high/low = MAX(high)/MIN(low) over the trailing 1-year window.
The API server reads this view for /api/indices (yearHigh/yearLow).

CLI:
    python3 -m backend.fetch_indices [--start YYYY-MM-DD] [--end YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys

from .db import get_connection, initialize_database
from .fetch_daily import default_start, get_checkpoint, set_checkpoint
from .openalgo_client import CredentialsNotConfigured, OpenAlgoClient, normalize_history

JOB = "daily_indices"

SNAPSHOT_VIEW_SQL = """
CREATE OR REPLACE VIEW index_snapshot AS
WITH latest AS (
    SELECT symbol, date, open, high, low, close,
           ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) AS rn
    FROM index_daily
),
year_stats AS (
    SELECT symbol, MAX(high) AS year_high, MIN(low) AS year_low
    FROM index_daily
    WHERE date >= (SELECT MAX(date) FROM index_daily) - INTERVAL '1 year'
    GROUP BY symbol
)
SELECT m.symbol,
       m.name,
       m.exchange,
       m.category,
       l.open,
       l.high,
       l.low,
       l.close,
       y.year_high,
       y.year_low,
       l.date AS as_of
FROM index_master m
LEFT JOIN latest l ON l.symbol = m.symbol AND l.rn = 1
LEFT JOIN year_stats y ON y.symbol = m.symbol
"""


def ensure_snapshot_view(con) -> None:
    """Create/refresh the index_snapshot view (latest OHLC + 52-week high/low)."""
    con.execute(SNAPSHOT_VIEW_SQL)


def pending_indices(con, job: str) -> list[tuple[str, str]]:
    """Active indices ordered by sort_order (alphabetical), after checkpoint."""
    rows = con.execute(
        "SELECT symbol, exchange FROM index_master WHERE active ORDER BY sort_order"
    ).fetchall()
    last = get_checkpoint(con, job)
    if last is not None:
        rows = [r for r in rows if r[0] > last]
    return rows


def upsert_index_bars(con, symbol: str, bars: list[dict]) -> int:
    con.executemany(
        "INSERT INTO index_daily (symbol, date, open, high, low, close)"
        " VALUES (?, ?, ?, ?, ?, ?)"
        " ON CONFLICT (symbol, date) DO UPDATE SET open = excluded.open,"
        " high = excluded.high, low = excluded.low, close = excluded.close",
        [(symbol, b["date"], b["open"], b["high"], b["low"], b["close"]) for b in bars],
    )
    return len(bars)


def run(start: str, end: str) -> int:
    initialize_database()
    con = get_connection()
    try:
        ensure_snapshot_view(con)
        todo = pending_indices(con, JOB)
    finally:
        con.close()
    if not todo:
        print("No active indices to fetch.")
        return 0

    client = OpenAlgoClient()
    print(f"Fetching daily OHLC for {len(todo)} indices ({start} -> {end}),"
          f" alphabetical via sort_order, interval 'D'.")
    total = 0
    for symbol, exchange in todo:
        con = get_connection()
        try:
            payload = client.history(symbol, exchange, start, end)
            bars = normalize_history(payload)
            n = upsert_index_bars(con, symbol, bars)
            set_checkpoint(con, JOB, symbol)
            total += n
            print(f"  {symbol} ({exchange}): {n} daily bars")
        finally:
            con.close()
    con = get_connection()
    try:
        ensure_snapshot_view(con)
    finally:
        con.close()
    print(f"Done. {total} bars upserted across {len(todo)} indices;"
          " index_snapshot view refreshed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m backend.fetch_indices",
        description="Fetch daily OHLC for every index in index_master"
                    " (alphabetical, checkpointed, daily interval only) and"
                    " refresh the index_snapshot 52-week high/low view.",
    )
    parser.add_argument("--start", default=default_start(),
                        help="start date YYYY-MM-DD (default: 10 years ago)")
    parser.add_argument("--end", default=dt.date.today().isoformat(),
                        help="end date YYYY-MM-DD (default: today)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args.start, args.end)
    except CredentialsNotConfigured as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
