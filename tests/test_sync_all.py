"""P4-C: one-command seed CLI (backend.sources.sync_all).

Fully offline: source syncs are replaced by fakes at the ``_load_sync``
seam (missing keys / unreachable endpoints are clean skips, not crashes);
one test exercises the real MoSPI no-key skip path, which never touches
the network.
"""

from __future__ import annotations

import pytest

from backend.db import get_connection, initialize_database
from backend.ingestion import ingestion_run
from backend.macro import upsert_observation
from backend.settings import get_settings
from backend.sources import mospi, sync_all


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("OGD_API_KEY", raising=False)
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    get_settings.cache_clear()
    initialize_database()
    con = get_connection()
    yield con
    con.close()
    get_settings.cache_clear()


def _fake_sync(label, writes=0, skipped=()):
    """A fail-soft source sync stand-in: writes real rows inside a real
    ingestion_run, then returns a source-style summary dict."""

    def sync(con):
        with ingestion_run(con, f"{label}_job") as run:
            for i in range(writes):
                upsert_observation(con, "cpi_inflation", f"2026-{i + 1:02d}", 5.0 + i)
                run.rows_written += 1
            if skipped:
                run.error = "; ".join(skipped)
        return {"synced": writes, "skipped": list(skipped)}

    return sync


def _patch_sources(monkeypatch, mapping):
    monkeypatch.setattr(sync_all, "_load_sync", lambda path: mapping[path])


def test_sync_all_offline_skips_exit_zero(db, monkeypatch, capsys):
    _patch_sources(
        monkeypatch,
        {
            "backend.sources.rbi": _fake_sync("rbi", writes=2),
            "backend.sources.intl": _fake_sync("intl", skipped=["us_fed_funds: no key"]),
            "backend.sources.mospi": _fake_sync("mospi", skipped=["cpi_inflation: no key"]),
            "backend.sources.nse_open": _fake_sync("nse_open"),
        },
    )
    assert sync_all.main([]) == 0
    out = capsys.readouterr().out
    assert "SYNC_ALL OK" in out
    assert "data-quality:" in out
    for label in ("rbi", "intl", "mospi", "nse_open"):
        assert label in out

    # audit trail: one ingestion run per fake source + the reconcile run,
    # and reconcile wrote data_quality rows (never-synced info rows etc.)
    jobs = {r[0] for r in db.execute("SELECT job FROM ingestion_runs").fetchall()}
    assert {"rbi_job", "intl_job", "mospi_job", "nse_open_job", "reconcile"} <= jobs
    assert db.execute("SELECT COUNT(*) FROM data_quality").fetchone()[0] > 0
    # the fake rbi sync really wrote through the validated upsert helper
    assert db.execute("SELECT COUNT(*) FROM macro_observations").fetchone()[0] == 2


def test_sync_all_hard_failure_exits_one(db, monkeypatch, capsys):
    def boom(con):
        raise RuntimeError("database gone")

    _patch_sources(
        monkeypatch,
        {
            "backend.sources.rbi": boom,
            "backend.sources.intl": _fake_sync("intl"),
            "backend.sources.mospi": _fake_sync("mospi"),
            "backend.sources.nse_open": _fake_sync("nse_open"),
        },
    )
    assert sync_all.main([]) == 1
    out = capsys.readouterr().out
    assert "SYNC_ALL FAILED" in out
    assert "failed" in out
    # reconcile still ran despite the crashed source
    assert "data-quality:" in out


def test_mospi_no_key_skips_without_network(db):
    # Real fail-soft path: no OGD_API_KEY -> clean skip, no HTTP at all.
    summary = mospi.sync(db)
    assert summary["synced"] == {}
    assert summary["skipped"]  # every configured resource skipped
