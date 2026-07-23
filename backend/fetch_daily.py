"""Daily OHLCV puller for all active securities.

Rate-limit policy (db_config.json -> fetch_policy):
  * daily timeframe only (interval "D" is hardcoded in the client)
  * symbols processed in STRICT alphabetical order
  * after each symbol completes, fetch_checkpoint (job="daily_equity") is
    upserted with that symbol; an interrupted run resumes at the symbol
    after the checkpoint
  * weekends/holidays need no calendar — the API simply returns no rows

CLI:
    python3 -m backend.fetch_daily [--start YYYY-MM-DD] [--end YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys

from .db import get_connection, initialize_database, load_config
from .openalgo_client import CredentialsNotConfigured, OpenAlgoClient, normalize_history

JOB = "daily_equity"


def default_start() -> str:
    return (dt.date.today() - dt.timedelta(days=365 * 10)).isoformat()


def get_checkpoint(con, job: str) -> str | None:
    row = con.execute(
        "SELECT last_symbol FROM fetch_checkpoint WHERE job = ?", (job,)
    ).fetchone()
    return row[0] if row else None


def set_checkpoint(con, job: str, symbol: str) -> None:
    con.execute(
        "INSERT INTO fetch_checkpoint (job, last_symbol, updated_at) VALUES (?, ?, now())"
        " ON CONFLICT (job) DO UPDATE SET last_symbol = excluded.last_symbol,"
        " updated_at = excluded.updated_at",
        (job, symbol),
    )


def upsert_bars(con, symbol: str, exchange: str, bars: list[dict]) -> int:
    con.executemany(
        "INSERT INTO daily_ohlcv (symbol, exchange, date, open, high, low, close, volume)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT (symbol, exchange, date) DO UPDATE SET open = excluded.open,"
        " high = excluded.high, low = excluded.low, close = excluded.close,"
        " volume = excluded.volume",
        [(symbol, exchange, b["date"], b["open"], b["high"], b["low"], b["close"],
          b["volume"]) for b in bars],
    )
    return len(bars)


def pending_symbols(con, job: str) -> list[tuple[str, str]]:
    """Active securities in strict alphabetical order, after the checkpoint."""
    rows = con.execute(
        "SELECT symbol, exchange FROM securities WHERE active ORDER BY symbol"
    ).fetchall()
    last = get_checkpoint(con, job)
    if last is not None:
        rows = [r for r in rows if r[0] > last]
    return rows


def run(start: str, end: str) -> int:
    initialize_database()
    config = load_config()
    checkpoint_table = config["fetch_policy"]["checkpoint_table"]
    assert checkpoint_table == "fetch_checkpoint"
    con = get_connection()
    try:
        todo = pending_symbols(con, JOB)
    finally:
        con.close()
    if not todo:
        print("No active securities to fetch (securities table empty or fully synced).")
        return 0

    client = OpenAlgoClient()
    print(f"Fetching daily OHLCV for {len(todo)} securities ({start} -> {end}),"
          f" strict alphabetical order, interval 'D'.")
    total = 0
    for symbol, exchange in todo:
        con = get_connection()
        try:
            payload = client.history(symbol, exchange, start, end)
            bars = normalize_history(payload)
            n = upsert_bars(con, symbol, exchange, bars)
            set_checkpoint(con, JOB, symbol)
            total += n
            print(f"  {symbol} ({exchange}): {n} daily bars")
        finally:
            con.close()
    print(f"Done. {total} bars upserted across {len(todo)} symbols.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m backend.fetch_daily",
        description="Fetch daily OHLCV for all active securities (alphabetical,"
                    " checkpointed, daily interval only).",
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
