"""Benchmark series registry + observation upsert helpers (P4-A).

The registry lives in db_config.json -> benchmarks and is seeded into the
`benchmark_series` table by backend.db.initialize_database(). Observations
are date-keyed (one value per series per day) and are written by the source
fetchers in backend/sources/ (RBI DBIE, US Treasury, FRED) — never manually
fabricated (SPEC: null when unsynced).
"""

from __future__ import annotations

from typing import Any

from .db import load_config


def registry() -> list[dict[str, Any]]:
    """Benchmark series registry from db_config.json (flat list of series)."""
    rows: list[dict[str, Any]] = []
    for group in load_config()["benchmarks"]:
        for series in group["series"]:
            rows.append(
                {
                    "key": series["key"],
                    "name": series["name"],
                    "unit": group["unit"],
                    "group": group["key"],
                }
            )
    return rows


def _known_keys(con) -> set[str]:
    return {r[0] for r in con.execute("SELECT key FROM benchmark_series").fetchall()}


def upsert_benchmark_observation(con, series_key: str, date: str, value: float) -> None:
    """Insert or update one benchmark observation; series_key must be registered.

    ``date`` is an ISO calendar date (YYYY-MM-DD) — benchmark series are
    date-keyed per the SPEC's daily discipline.
    """
    if series_key not in _known_keys(con):
        raise KeyError(
            f"unknown benchmark series '{series_key}' — register it in"
            " db_config.json -> benchmarks and re-run backend.db"
        )
    con.execute(
        "INSERT INTO benchmark_observations (series_key, date, value) VALUES (?, ?, ?)"
        " ON CONFLICT (series_key, date) DO UPDATE SET value = excluded.value",
        (series_key, str(date), float(value)),
    )
