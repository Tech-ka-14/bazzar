"""DuckDB bootstrap for the Bazzar Terminal data layer.

`backend/db_config.json` is the single database setup configuration file:
every table, the full index universe, the macro indicator registry, the
benchmark series, and the fetch policy are defined there. The entire
database is created from — and only from — that file.

Usage:
    python3 -m backend.db          # create/seed the database and print a summary
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

import duckdb

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
DEFAULT_CONFIG_PATH = PACKAGE_DIR / "db_config.json"


def load_config(path: Optional[str] = None) -> dict[str, Any]:
    """Load the database setup configuration (defaults to backend/db_config.json)."""
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    with open(config_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def get_data_dir() -> Path:
    """Data directory holding bazzar.duckdb and the chart cache.

    Overridable with the BAZZAR_DATA_DIR environment variable; defaults to
    ./data relative to the repo root (per db_config.json -> database.path).
    """
    env = os.environ.get("BAZZAR_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()
    db_rel = Path(load_config()["database"]["path"])  # e.g. data/bazzar.duckdb
    return (REPO_ROOT / db_rel).parent


def get_db_path() -> Path:
    config = load_config()
    return get_data_dir() / Path(config["database"]["path"]).name


def get_connection(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection to the configured database file."""
    db_path = get_db_path()
    if not read_only:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path), read_only=read_only)


def _create_table_sql(name: str, spec: dict[str, Any]) -> str:
    cols = ", ".join(f"{c['name']} {c['type']}" for c in spec["columns"])
    pk = spec.get("primary_key")
    if pk:
        cols += f", PRIMARY KEY ({', '.join(pk)})"
    return f"CREATE TABLE IF NOT EXISTS {name} ({cols})"


def _seed_index_master(con: duckdb.DuckDBPyConnection, config: dict[str, Any]) -> int:
    indices = sorted(config["indices"], key=lambda d: d["sort_order"])
    con.execute("DELETE FROM index_master")
    con.executemany(
        "INSERT INTO index_master (symbol, name, exchange, category, active, sort_order)"
        " VALUES (?, ?, ?, ?, TRUE, ?)",
        [(d["symbol"], d["name"], d["exchange"], d["category"], d["sort_order"])
         for d in indices],
    )
    return len(indices)


def _seed_macro_series(con: duckdb.DuckDBPyConnection, config: dict[str, Any]) -> int:
    entries = config["macro_indicators"]
    con.execute("DELETE FROM macro_series")
    con.executemany(
        "INSERT INTO macro_series (key, title, category, unit, frequency, source, source_url)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(m["key"], m["title"], m["category"], m["unit"], m["frequency"],
          m["source"], m["source_url"]) for m in entries],
    )
    return len(entries)


def _seed_benchmark_series(con: duckdb.DuckDBPyConnection, config: dict[str, Any]) -> int:
    con.execute("DELETE FROM benchmark_series")
    count = 0
    for group in config["benchmarks"]:
        for series in group["series"]:
            con.execute(
                "INSERT INTO benchmark_series (key, name, unit) VALUES (?, ?, ?)",
                (series["key"], series["name"], group["unit"]),
            )
            count += 1
    return count


def initialize_database(config_path: Optional[str] = None) -> dict[str, int]:
    """Create every table defined in db_config.json and seed the config-derived
    reference tables (index_master, macro_series, benchmark_series).

    Idempotent: tables use CREATE TABLE IF NOT EXISTS and the seed tables are
    fully rebuilt from the config on every run.
    """
    config = load_config(config_path)
    con = get_connection()
    try:
        for name, spec in config["tables"].items():
            con.execute(_create_table_sql(name, spec))
        summary = {
            "tables": len(config["tables"]),
            "index_master": _seed_index_master(con, config),
            "macro_series": _seed_macro_series(con, config),
            "benchmark_series": _seed_benchmark_series(con, config),
        }
    finally:
        con.close()
    return summary


def main() -> None:
    summary = initialize_database()
    db_path = get_db_path()
    print(f"Initialized Bazzar database at {db_path}")
    print(f"  tables created : {summary['tables']}")
    print(f"  index_master   : {summary['index_master']} indices seeded")
    print(f"  macro_series   : {summary['macro_series']} indicators seeded")
    print(f"  benchmark_series: {summary['benchmark_series']} series seeded")


if __name__ == "__main__":
    main()
