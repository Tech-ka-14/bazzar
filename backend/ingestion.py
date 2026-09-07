"""Ingestion audit trail (``ingestion_runs`` table, migration 0002).

Every fetch/import job wraps its work in :func:`ingestion_run`, which records
start/finish times, rows written/rejected, final status and any error. This
powers ``asOf``/staleness reporting across the API (SPEC: every number
carries asOf + source) and the UI "data is N days stale" badge.

Usage:
    with ingestion_run(con, "daily_equity") as run:
        ...
        run.rows_written += n
        run.rows_rejected += r
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import duckdb

from .logging_config import get_logger

logger = get_logger("ingestion")


@dataclass
class RunHandle:
    """Mutable counters a job updates while running."""

    run_id: int
    job: str
    rows_written: int = 0
    rows_rejected: int = 0


@contextmanager
def ingestion_run(con: duckdb.DuckDBPyConnection, job: str) -> Iterator[RunHandle]:
    """Record one ingestion job run; status is success/failed on exit."""
    started = dt.datetime.now(dt.UTC).replace(tzinfo=None)
    row = con.execute(
        "INSERT INTO ingestion_runs (job, started_at, status) VALUES (?, ?, 'running')"
        " RETURNING run_id",
        (job, started),
    ).fetchone()
    assert row is not None
    handle = RunHandle(run_id=int(row[0]), job=job)
    try:
        yield handle
    except Exception as exc:
        con.execute(
            "UPDATE ingestion_runs SET finished_at = now(), rows_written = ?,"
            " rows_rejected = ?, status = 'failed', error = ? WHERE run_id = ?",
            (handle.rows_written, handle.rows_rejected, str(exc)[:1000], handle.run_id),
        )
        logger.error("ingestion run failed", job=job, run_id=handle.run_id, error=str(exc))
        raise
    else:
        con.execute(
            "UPDATE ingestion_runs SET finished_at = now(), rows_written = ?,"
            " rows_rejected = ?, status = 'success' WHERE run_id = ?",
            (handle.rows_written, handle.rows_rejected, handle.run_id),
        )
        logger.info(
            "ingestion run finished",
            job=job,
            run_id=handle.run_id,
            rows_written=handle.rows_written,
            rows_rejected=handle.rows_rejected,
        )


def latest_runs(con: duckdb.DuckDBPyConnection, limit: int = 50) -> list[dict[str, Any]]:
    """Most recent ingestion runs, newest first."""
    rows = con.execute(
        "SELECT run_id, job, started_at, finished_at, rows_written, rows_rejected,"
        " status, error FROM ingestion_runs ORDER BY run_id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    cols = [
        "run_id",
        "job",
        "started_at",
        "finished_at",
        "rows_written",
        "rows_rejected",
        "status",
        "error",
    ]
    return [dict(zip(cols, r, strict=True)) for r in rows]


def data_freshness(con: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    """Per job: last run status/timestamps plus the data asOf date.

    asOf is the newest data date written by that job (never fabricated —
    null when nothing has been synced yet).
    """
    jobs = [r[0] for r in con.execute("SELECT DISTINCT job FROM ingestion_runs").fetchall()]
    data_asof_queries = {
        "daily_equity": "SELECT MAX(date) FROM daily_ohlcv",
        "daily_indices": "SELECT MAX(date) FROM index_daily",
    }
    report: list[dict[str, Any]] = []
    for job in sorted(jobs):
        last = con.execute(
            "SELECT started_at, finished_at, rows_written, rows_rejected, status, error"
            " FROM ingestion_runs WHERE job = ? ORDER BY run_id DESC LIMIT 1",
            (job,),
        ).fetchone()
        as_of = None
        if job in data_asof_queries:
            row = con.execute(data_asof_queries[job]).fetchone()
            as_of = str(row[0])[:10] if row and row[0] is not None else None
        report.append(
            {
                "job": job,
                "last_started_at": str(last[0]) if last else None,
                "last_finished_at": str(last[1]) if last else None,
                "last_rows_written": last[2] if last else None,
                "last_rows_rejected": last[3] if last else None,
                "last_status": last[4] if last else None,
                "last_error": last[5] if last else None,
                "data_as_of": as_of,
            }
        )
    return report
