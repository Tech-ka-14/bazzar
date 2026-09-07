"""P2: schema migration runner tests."""

from __future__ import annotations

import pytest

from backend.db import get_connection, initialize_database
from backend.migrate import applied_versions, migrate_to_latest, migration_status


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    summary = initialize_database()
    yield tmp_path, summary


def test_baseline_migrations_applied(fresh_db):
    _, summary = fresh_db
    assert summary["migrations_applied"] >= 2  # 0001_init + 0002_ops_tables
    con = get_connection(read_only=True)
    try:
        assert {1, 2} <= applied_versions(con)
    finally:
        con.close()


def test_migrations_are_idempotent(fresh_db):
    con = get_connection()
    try:
        assert migrate_to_latest(con) == []  # second run applies nothing
    finally:
        con.close()


def test_ops_tables_exist(fresh_db):
    con = get_connection(read_only=True)
    try:
        tables = {
            r[0]
            for r in con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()
        }
    finally:
        con.close()
    assert {"schema_migrations", "data_rejects", "ingestion_runs", "trading_calendar"} <= tables


def test_migration_status_reports_applied(fresh_db):
    con = get_connection(read_only=True)
    try:
        status = migration_status(con)
    finally:
        con.close()
    assert status and all(entry["applied"] for entry in status)
    assert [entry["version"] for entry in status] == sorted(entry["version"] for entry in status)
