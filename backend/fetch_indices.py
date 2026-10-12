"""Daily OHLC puller for the full index universe (index_master).

Same checkpoint discipline as fetch_daily (job="daily_indices"): symbols are
processed in alphabetical order (index_master.sort_order is assigned
alphabetically), and fetch_checkpoint records the last completed symbol so an
interrupted run resumes at the next one.

Provider selection (P3) matches fetch_daily: ``--provider`` or the
MARKET_DATA_PROVIDER setting. Kite resolves index instrument tokens from the
securities table (run `python -m backend.sync_instruments --provider kite`
first — index instruments are stored under the *_INDEX exchange labels).

Also maintains the `index_snapshot` helper view, which computes per index:
latest daily OHLC (as of the most recent date in index_daily) plus the
52-week (year) high/low = MAX(high)/MIN(low) over the trailing 1-year window.
The API server reads this view for /api/indices (yearHigh/yearLow).

CLI:
    python3 -m backend.fetch_indices [--start YYYY-MM-DD] [--end YYYY-MM-DD]
                                     [--provider kite|openalgo|nse_bhavcopy]
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys

from .db import get_connection, initialize_database
from .fetch_daily import default_start, get_checkpoint, set_checkpoint
from .ingestion import ingestion_run
from .providers import PROVIDERS, ProviderAuthRequired, ProviderError, get_provider
from .providers.openalgo import CredentialsNotConfigured
from .validation import upsert_index_daily

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
    """Legacy shim — delegates to the validated write path (P2)."""
    written, _ = upsert_index_daily(con, job=JOB, symbol=symbol, exchange="IDX", bars=bars)
    return written


def run(start: str, end: str, provider_name: str | None = None) -> int:
    initialize_database()
    con = get_connection()
    try:
        ensure_snapshot_view(con)
        todo = pending_indices(con, JOB)
        provider = get_provider(provider_name, con=con)
    finally:
        con.close()
    if not todo:
        print("No active indices to fetch.")
        return 0

    print(
        f"Fetching daily OHLC for {len(todo)} indices ({start} -> {end})"
        f" via provider '{provider.name}', alphabetical via sort_order, daily only."
    )
    con = get_connection()
    total = 0
    total_rejected = 0
    failed: list[str] = []
    try:
        with ingestion_run(con, JOB) as run:
            for symbol, exchange in todo:
                try:
                    bars = provider.history_daily(symbol, exchange, start, end)
                except ProviderAuthRequired:
                    raise  # abort the run — re-authenticate, checkpoint stays put
                except Exception as exc:  # per-symbol failure: skip, keep going
                    failed.append(f"{symbol} ({exc.__class__.__name__})")
                    print(f"  {symbol} ({exchange}): FAILED — {exc}; skipping")
                    set_checkpoint(con, JOB, symbol)
                    continue
                written, rejected = upsert_index_daily(
                    con, job=JOB, symbol=symbol, exchange=exchange, bars=bars
                )
                set_checkpoint(con, JOB, symbol)
                run.rows_written += written
                run.rows_rejected += rejected
                total += written
                total_rejected += rejected
                print(f"  {symbol} ({exchange}): {written} daily bars, {rejected} rejected")
            if failed:
                run.error = f"{len(failed)} index symbol(s) failed: {', '.join(failed[:20])}"
        ensure_snapshot_view(con)
    finally:
        con.close()
    print(
        f"Done. {total} bars upserted across {len(todo) - len(failed)} indices"
        f" ({total_rejected} rows quarantined); index_snapshot view refreshed."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m backend.fetch_indices",
        description="Fetch daily OHLC for every index in index_master"
        " (alphabetical, checkpointed, daily interval only) and"
        " refresh the index_snapshot 52-week high/low view.",
    )
    parser.add_argument(
        "--start", default=default_start(), help="start date YYYY-MM-DD (default: 10 years ago)"
    )
    parser.add_argument(
        "--end", default=dt.date.today().isoformat(), help="end date YYYY-MM-DD (default: today)"
    )
    parser.add_argument(
        "--provider",
        choices=PROVIDERS,
        default=None,
        help="market-data provider (default: MARKET_DATA_PROVIDER setting, 'openalgo')",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args.start, args.end, provider_name=args.provider)
    except CredentialsNotConfigured as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ProviderAuthRequired as exc:
        print(
            f"error: {exc}\nRe-authenticate, then rerun — the checkpoint resumes.", file=sys.stderr
        )
        return 3
    except ProviderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
