"""Instrument-master sync (P3, roadmap 3.3).

Pulls the provider's security master (Kite ``instruments("NSE")/("BSE")``)
and upserts it into the ``securities`` table — including ``instrument_token``,
``lot_size`` and ``tick_size`` (migration 0003), which the Kite provider needs
for historical-data calls.

Semantics:
  * keeps equity instruments (instrument_type EQ) and index instruments
    (segment INDICES → exchange "NSE_INDEX"/"BSE_INDEX", type INDEX);
    derivatives etc. are skipped;
  * upsert key is (symbol, exchange); rows are NEVER deleted — instruments
    that vanish from the master and have an instrument_token are marked
    ``active = FALSE`` (checkpoint/history stays intact);
  * symbols are uppercased; ISIN is preserved from the existing row when the
    provider leaves it blank;
  * every run is audited via ingestion_runs (job="instrument_sync").

CLI:
    python -m backend.sync_instruments [--provider kite]
"""

from __future__ import annotations

import argparse
import sys

import duckdb

from .db import get_connection, initialize_database
from .ingestion import ingestion_run
from .providers import PROVIDERS, MarketDataProvider, ProviderAuthRequired, get_provider

JOB = "instrument_sync"
DEFAULT_EXCHANGES = ("NSE", "BSE")


def target_exchange(exchange: str, segment: str) -> str:
    """Kite lists index instruments on the base exchange with segment
    INDICES — Bazzar stores them under the *_INDEX exchange label."""
    return f"{exchange}_INDEX" if segment.upper() == "INDICES" else exchange


def sync_instruments(
    con: duckdb.DuckDBPyConnection,
    provider: MarketDataProvider,
    exchanges: tuple[str, ...] = DEFAULT_EXCHANGES,
) -> dict[str, int]:
    """Upsert the provider's instrument master into ``securities``.

    Returns stats: {written, skipped, deactivated}.
    """
    written = 0
    skipped = 0
    seen: list[tuple[str, str]] = []
    with ingestion_run(con, JOB) as run:
        for exchange in exchanges:
            for inst in provider.instruments(exchange):
                target = target_exchange(inst.exchange, inst.segment)
                itype = (inst.instrument_type or "").upper()
                is_index = target.endswith("_INDEX")
                if not is_index and itype != "EQ":
                    skipped += 1
                    continue
                symbol = inst.symbol.upper()
                if not symbol:
                    skipped += 1
                    continue
                con.execute(
                    "INSERT INTO securities"
                    " (symbol, name, exchange, instrument_type, isin, active,"
                    "  instrument_token, lot_size, tick_size)"
                    " VALUES (?, ?, ?, ?, ?, TRUE, ?, ?, ?)"
                    " ON CONFLICT (symbol, exchange) DO UPDATE SET"
                    "  name = excluded.name,"
                    "  instrument_type = excluded.instrument_type,"
                    "  isin = COALESCE(excluded.isin, securities.isin),"
                    "  active = TRUE,"
                    "  instrument_token = excluded.instrument_token,"
                    "  lot_size = excluded.lot_size,"
                    "  tick_size = excluded.tick_size",
                    (
                        symbol,
                        inst.name or symbol,
                        target,
                        "INDEX" if is_index else "EQ",
                        inst.isin,
                        inst.instrument_token,
                        inst.lot_size,
                        inst.tick_size,
                    ),
                )
                seen.append((symbol, target))
                written += 1
        # Deactivate (never delete) instruments that vanished from the master.
        deactivated = 0
        if seen:
            placeholders = ", ".join(["(?, ?)"] * len(seen))
            flat = [v for pair in seen for v in pair]
            result = con.execute(
                "UPDATE securities SET active = FALSE"
                " WHERE active AND instrument_token IS NOT NULL"
                f" AND (symbol, exchange) NOT IN ({placeholders})",
                flat,
            ).fetchone()
            deactivated = int(result[0]) if result else 0
        run.rows_written = written
        run.rows_rejected = skipped
    return {"written": written, "skipped": skipped, "deactivated": deactivated}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m backend.sync_instruments",
        description="Sync the provider's instrument master into the securities table.",
    )
    parser.add_argument(
        "--provider",
        choices=PROVIDERS,
        default=None,
        help="market-data provider (default: MARKET_DATA_PROVIDER setting)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    initialize_database()
    con = get_connection()
    try:
        try:
            provider = get_provider(args.provider, con=con)
        except ProviderAuthRequired as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 3
        stats = sync_instruments(con, provider)
    finally:
        con.close()
    print(
        f"instrument_sync: {stats['written']} upserted, {stats['skipped']} skipped,"
        f" {stats['deactivated']} deactivated."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
