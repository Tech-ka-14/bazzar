"""Schema migration runner for the Bazzar Terminal data layer.

Migrations are plain SQL files in ``backend/migrations/`` named
``NNNN_description.sql``. They are applied in version order, each inside its
own transaction, and recorded in the ``schema_migrations`` table. Applied
migrations are never re-run; new migrations are picked up automatically at
startup via :func:`backend.db.initialize_database`.

Rules:
  * never edit an already-applied migration — add a new one instead
  * migrations must be idempotent where possible (CREATE ... IF NOT EXISTS)
    so a crash mid-apply can simply be retried
"""

from __future__ import annotations

import re
from pathlib import Path

import duckdb

from .db import get_connection

PACKAGE_DIR = Path(__file__).resolve().parent
MIGRATIONS_DIR = PACKAGE_DIR / "migrations"

_VERSION_RE = re.compile(r"^(\d{4,})_.+\.sql$")

_CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT now()
)
"""


def _split_statements(script: str) -> list[str]:
    """Split a SQL script into statements on semicolons at line ends.

    Line comments (--) are stripped first. Sufficient for the plain DDL used
    in this project (no procedures / string-embedded semicolons).
    """
    cleaned = "\n".join(line for line in script.splitlines() if not line.strip().startswith("--"))
    return [stmt.strip() for stmt in cleaned.split(";") if stmt.strip()]


def list_migrations(migrations_dir: Path | None = None) -> list[tuple[int, str, Path]]:
    """All migration files as (version, name, path), sorted by version."""
    directory = migrations_dir or MIGRATIONS_DIR
    found: list[tuple[int, str, Path]] = []
    for path in sorted(directory.glob("*.sql")):
        match = _VERSION_RE.match(path.name)
        if not match:
            raise ValueError(f"migration filename does not match NNNN_name.sql: {path.name}")
        found.append((int(match.group(1)), path.stem, path))
    versions = [v for v, _, _ in found]
    if len(set(versions)) != len(versions):
        raise ValueError(f"duplicate migration versions in {directory}")
    return found


def applied_versions(con: duckdb.DuckDBPyConnection) -> set[int]:
    exists = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables"
        " WHERE table_schema = 'main' AND table_name = 'schema_migrations'"
    ).fetchone()
    if not exists or exists[0] == 0:
        # Read-only connections cannot CREATE; for them "no table" simply
        # means "nothing applied yet" (migrate_to_latest requires a
        # read-write connection anyway).
        try:
            con.execute(_CREATE_MIGRATIONS_TABLE)
        except duckdb.InvalidInputException:
            return set()
        return set()
    rows = con.execute("SELECT version FROM schema_migrations").fetchall()
    return {r[0] for r in rows}


def migrate_to_latest(
    con: duckdb.DuckDBPyConnection | None = None,
    migrations_dir: Path | None = None,
) -> list[tuple[int, str]]:
    """Apply all pending migrations in order. Returns newly applied (version, name)."""
    own = con is None
    if own:
        con = get_connection()
    assert con is not None
    newly_applied: list[tuple[int, str]] = []
    try:
        done = applied_versions(con)
        for version, name, path in list_migrations(migrations_dir):
            if version in done:
                continue
            script = path.read_text(encoding="utf-8")
            con.execute("BEGIN TRANSACTION")
            try:
                for statement in _split_statements(script):
                    con.execute(statement)
                con.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                    (version, name),
                )
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise
            newly_applied.append((version, name))
    finally:
        if own:
            con.close()
    return newly_applied


def migration_status(con: duckdb.DuckDBPyConnection | None = None) -> list[dict[str, object]]:
    """Every migration file with its applied state (for health/diagnostics)."""
    own = con is None
    if own:
        con = get_connection()
    assert con is not None
    try:
        done = applied_versions(con)
        return [{"version": v, "name": n, "applied": v in done} for v, n, _ in list_migrations()]
    finally:
        if own:
            con.close()


def main() -> None:
    applied = migrate_to_latest()
    if applied:
        for version, name in applied:
            print(f"applied {name} (version {version})")
    else:
        print("schema already up to date")


if __name__ == "__main__":
    main()
