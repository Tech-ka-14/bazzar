"""Backup & restore for the DuckDB data store.

``python -m backend.backup create`` exports every table to a timestamped
parquet snapshot under ``<data dir>/backups/YYYYMMDD_HHMMSS/`` (DuckDB
``EXPORT DATABASE``), then enforces retention (last 14 daily snapshots +
one monthly snapshot for each of the last 12 months) and checkpoints the
live database.

``python -m backend.backup restore <snapshot_dir> --db <path>`` imports a
snapshot into a fresh database file (``IMPORT DATABASE``) — used by the
round-trip test and for disaster recovery.

Idempotent and cron-able: snapshots are immutable once written; creating a
snapshot twice in the same second simply re-exports.
"""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sys
from pathlib import Path

import duckdb

from .db import get_connection, get_data_dir
from .logging_config import get_logger

logger = get_logger("backup")

RETAIN_DAILY = 14
RETAIN_MONTHLY = 12


def backups_root() -> Path:
    return get_data_dir() / "backups"


def _snapshot_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        (p for p in root.iterdir() if p.is_dir() and _parse_ts(p.name) is not None),
        key=lambda p: p.name,
    )


def _parse_ts(name: str) -> dt.datetime | None:
    try:
        return dt.datetime.strptime(name, "%Y%m%d_%H%M%S")
    except ValueError:
        return None


def apply_retention(root: Path | None = None) -> list[Path]:
    """Delete snapshots beyond retention; returns the deleted directories."""
    root = root or backups_root()
    snapshots = _snapshot_dirs(root)
    keep: set[Path] = set(snapshots[-RETAIN_DAILY:])

    # Newest snapshot per calendar month, for the last RETAIN_MONTHLY months.
    monthly: dict[tuple[int, int], Path] = {}
    for path in snapshots:
        ts = _parse_ts(path.name)
        assert ts is not None
        monthly[(ts.year, ts.month)] = path  # ascending order -> newest wins
    for key in sorted(monthly, reverse=True)[:RETAIN_MONTHLY]:
        keep.add(monthly[key])

    deleted: list[Path] = []
    for path in snapshots:
        if path not in keep:
            shutil.rmtree(path)
            deleted.append(path)
            logger.info("backup pruned by retention", path=str(path))
    return deleted


def create_backup(con: duckdb.DuckDBPyConnection | None = None) -> Path:
    """Export the database to a timestamped parquet snapshot; returns its path."""
    own = con is None
    if own:
        con = get_connection()
    assert con is not None
    root = backups_root()
    root.mkdir(parents=True, exist_ok=True)
    target = root / dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        con.execute(f"EXPORT DATABASE '{target}' (FORMAT PARQUET)")
        con.execute("CHECKPOINT")
    finally:
        if own:
            con.close()
    logger.info("backup created", path=str(target))
    apply_retention(root)
    return target


def restore_backup(snapshot_dir: str | Path, db_path: str | Path) -> dict[str, int]:
    """Import a snapshot into a (new) database file; returns per-table row counts."""
    snapshot = Path(snapshot_dir)
    if not (snapshot / "schema.sql").exists():
        raise FileNotFoundError(f"not a backup snapshot (no schema.sql): {snapshot}")
    db_path = Path(db_path)
    if db_path.exists():
        raise FileExistsError(f"restore target must be a new file: {db_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    try:
        con.execute(f"IMPORT DATABASE '{snapshot}'")
        tables = [
            r[0]
            for r in con.execute(
                "SELECT table_name FROM information_schema.tables"
                " WHERE table_schema = 'main' ORDER BY table_name"
            ).fetchall()
        ]
        counts = {
            t: con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]  # type: ignore[index]
            for t in tables
        }
    finally:
        con.close()
    logger.info("backup restored", snapshot=str(snapshot), db=str(db_path), tables=len(counts))
    return counts


def table_counts(con: duckdb.DuckDBPyConnection | None = None) -> dict[str, int]:
    """Per-table row counts of the live database (for round-trip comparison)."""
    own = con is None
    if own:
        con = get_connection(read_only=True)
    assert con is not None
    try:
        tables = [
            r[0]
            for r in con.execute(
                "SELECT table_name FROM information_schema.tables"
                " WHERE table_schema = 'main' ORDER BY table_name"
            ).fetchall()
        ]
        return {
            t: con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]  # type: ignore[index]
            for t in tables
        }
    finally:
        if own:
            con.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m backend.backup",
        description="Backup/restore the Bazzar DuckDB store as parquet snapshots.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("create", help="export a timestamped snapshot and apply retention")
    sub.add_parser("list", help="list snapshots")
    p_restore = sub.add_parser("restore", help="import a snapshot into a new database file")
    p_restore.add_argument("snapshot_dir")
    p_restore.add_argument("--db", required=True, help="path of the NEW duckdb file to create")
    args = parser.parse_args(argv)

    if args.command == "create":
        path = create_backup()
        print(f"Backup snapshot written to {path}")
    elif args.command == "list":
        for path in _snapshot_dirs(backups_root()):
            print(path)
    else:
        counts = restore_backup(args.snapshot_dir, args.db)
        for table, count in counts.items():
            print(f"  {table}: {count} rows")
        print(f"Restored {len(counts)} tables into {args.db}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
