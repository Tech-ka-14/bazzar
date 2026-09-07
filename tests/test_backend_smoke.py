"""Smoke tests for the backend package (SPEC verification contract)."""

from __future__ import annotations


def test_server_app_imports() -> None:
    from backend.server import app

    assert app.title == "Bazzar Terminal Data API"


def test_db_bootstrap_creates_tables(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    from backend import db

    db.initialize_database()
    con = db.get_connection()
    try:
        tables = {
            r[0] for r in con.execute("SELECT table_name FROM information_schema.tables").fetchall()
        }
    finally:
        con.close()
    assert {"securities", "daily_ohlcv", "fetch_checkpoint"} <= tables


def test_settings_validate(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    from backend.settings import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    assert 1 <= settings.bazzar_api_port <= 65535
    assert settings.bazzar_data_dir == tmp_path
    get_settings.cache_clear()
