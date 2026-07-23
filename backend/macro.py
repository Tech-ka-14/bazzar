"""Macro/micro indicator registry + observation import helpers.

The registry lives in db_config.json -> macro_indicators and is seeded into
the `macro_series` table by backend.db.initialize_database(). There is NO
scraping: observations are entered manually or imported from CSV after being
collected from the official sources listed in the registry (mospi.gov.in,
eaindustry.nic.in, rbi.org.in, cga.nic.in, commerce.gov.in, S&P Global PMI,
PLFS/MoSPI, siam.in, gst.gov.in/pib.gov.in, nhb.org.in, dpiit.gov.in).

CSV format (header required): series_key,period,value
  * series_key — a key from the registry (e.g. cpi_inflation)
  * period     — free-form period label, e.g. 2025-06, 2025-Q1, FY2024-25
  * value      — numeric observation in the registry unit

CLI:
    python3 -m backend.macro import observations.csv
    python3 -m backend.macro add <series_key> <period> <value>
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Optional

from .db import get_connection, initialize_database, load_config


def registry() -> list[dict[str, Any]]:
    """Macro indicator registry from db_config.json."""
    return load_config()["macro_indicators"]


def _known_keys(con) -> set[str]:
    return {r[0] for r in con.execute("SELECT key FROM macro_series").fetchall()}


def upsert_observation(con, series_key: str, period: str, value: float) -> None:
    """Insert or update one macro observation; series_key must be registered."""
    if series_key not in _known_keys(con):
        raise KeyError(
            f"unknown macro series '{series_key}' — register it in"
            " db_config.json -> macro_indicators and re-run backend.db"
        )
    con.execute(
        "INSERT INTO macro_observations (series_key, period, value) VALUES (?, ?, ?)"
        " ON CONFLICT (series_key, period) DO UPDATE SET value = excluded.value",
        (series_key, str(period), float(value)),
    )


def import_csv(path: str, con=None) -> int:
    """Import observations from a CSV (series_key,period,value). Returns row count."""
    own = con is None
    if own:
        initialize_database()
        con = get_connection()
    count = 0
    try:
        with open(Path(path), newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                key = (row.get("series_key") or row.get("key") or "").strip()
                period = (row.get("period") or "").strip()
                value = (row.get("value") or "").strip()
                if not key or not period or not value:
                    continue
                upsert_observation(con, key, period, float(value))
                count += 1
    finally:
        if own:
            con.close()
    return count


def latest_observations(con=None) -> list[dict[str, Any]]:
    """Latest + previous observation per registered series (never fabricated)."""
    own = con is None
    if own:
        con = get_connection()
    try:
        rows = con.execute(
            """
            WITH ranked AS (
                SELECT series_key, period, value,
                       ROW_NUMBER() OVER (PARTITION BY series_key ORDER BY period DESC) AS rn
                FROM macro_observations
            )
            SELECT s.key, s.title, s.category, s.unit, s.frequency, s.source, s.source_url,
                   cur.value AS latest, cur.period AS period,
                   prev.value AS previous
            FROM macro_series s
            LEFT JOIN ranked cur ON cur.series_key = s.key AND cur.rn = 1
            LEFT JOIN ranked prev ON prev.series_key = s.key AND prev.rn = 2
            ORDER BY s.category, s.key
            """
        ).fetchall()
        cols = ["key", "title", "category", "unit", "frequency", "source",
                "source_url", "latest", "period", "previous"]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        if own:
            con.close()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m backend.macro",
        description="Macro observation import helpers (no scraping — data is"
                    " entered/imported from the official sources in the registry).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p_import = sub.add_parser("import", help="import a CSV (series_key,period,value)")
    p_import.add_argument("csv_path")
    p_add = sub.add_parser("add", help="add a single observation")
    p_add.add_argument("series_key")
    p_add.add_argument("period")
    p_add.add_argument("value", type=float)
    args = parser.parse_args(argv)

    initialize_database()
    if args.command == "import":
        n = import_csv(args.csv_path)
        print(f"Imported {n} macro observations from {args.csv_path}")
    else:
        con = get_connection()
        try:
            upsert_observation(con, args.series_key, args.period, args.value)
        finally:
            con.close()
        print(f"Upserted {args.series_key} [{args.period}] = {args.value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
