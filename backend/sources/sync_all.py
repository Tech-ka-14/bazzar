"""One-command data seed (P4-C, roadmap 4.5): every P4 source + reconciliation.

    python3 -m backend.sources.sync_all

Runs, in order:
  1. RBI DBIE sync            (backend.sources.rbi.sync)
  2. International benchmarks (backend.sources.intl.sync — FRED is skipped
     without FRED_API_KEY)
  3. MoSPI via OGD            (backend.sources.mospi.sync — skipped without
     OGD_API_KEY)
  4. NSE open data            (backend.sources.nse_open.sync — holidays +
     FII/DII flows)
  5. Data-quality reconciliation (backend.reconcile.run_all)

Robustness contract (P4 acceptance command — must be robust offline):
missing API keys and unreachable endpoints are clean skips or partial runs
(the source modules already fail soft per series/dataset, never fabricate),
never crashes. The exit code is 1 ONLY on hard failures — a sync step or
the reconcile pass raising unexpectedly. Data-quality findings (warn/fail
rows) are reported but do not fail the command.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from typing import Any

from ..db import get_connection, initialize_database
from ..logging_config import get_logger
from ..reconcile import run_all

logger = get_logger("sources.sync_all")

# (label, import path) — imported lazily so a broken optional dependency in
# one source cannot stop the others from running.
_STEPS: tuple[tuple[str, str], ...] = (
    ("rbi", "backend.sources.rbi"),
    ("intl", "backend.sources.intl"),
    ("mospi", "backend.sources.mospi"),
    ("nse_open", "backend.sources.nse_open"),
)


def _load_sync(module_path: str) -> Callable[..., dict[str, Any]]:
    import importlib

    return importlib.import_module(module_path).sync


def _summarise(label: str, summary: dict[str, Any]) -> tuple[str, str]:
    """(status, detail) for one source summary dict."""
    skipped = list(summary.get("skipped") or [])
    detail = json.dumps(summary, sort_keys=True, default=str)
    if skipped:
        return "partial", f"skipped={','.join(skipped)} {detail}"
    return "ok", detail


def run(con) -> tuple[list[dict[str, Any]], dict[str, Any] | None, bool]:
    """Run all sync steps + reconcile. Returns (step results, reconcile
    summary, hard_failure)."""
    results: list[dict[str, Any]] = []
    hard_failure = False
    for label, module_path in _STEPS:
        try:
            summary = _load_sync(module_path)(con)
            status, detail = _summarise(label, summary)
        except Exception as exc:  # hard failure — source syncs fail soft by design
            logger.error("source sync crashed", source=label, error=str(exc))
            status, detail = "failed", f"{type(exc).__name__}: {exc}"
            hard_failure = True
        results.append({"source": label, "status": status, "detail": detail})

    reconcile_summary: dict[str, Any] | None = None
    try:
        reconcile_summary = run_all(con)
    except Exception as exc:
        logger.error("reconcile crashed", error=str(exc))
        results.append(
            {"source": "reconcile", "status": "failed", "detail": f"{type(exc).__name__}: {exc}"}
        )
        hard_failure = True
    return results, reconcile_summary, hard_failure


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m backend.sources.sync_all",
        description="Seed every P4 data source (RBI, international benchmarks,"
        " MoSPI/OGD, NSE open data) and run the data-quality reconciliation"
        " checks. Exit 1 only on hard failures; missing keys / offline"
        " sources are clean skips.",
    )
    parser.parse_args(argv)

    initialize_database()
    con = get_connection()
    try:
        results, reconcile_summary, hard_failure = run(con)
    finally:
        con.close()

    print(f"{'source':<12} {'status':<8} detail")
    print("-" * 72)
    for result in results:
        print(f"{result['source']:<12} {result['status']:<8} {result['detail']}")
    if reconcile_summary is not None:
        print("-" * 72)
        print(
            "data-quality: "
            f"checks_run={reconcile_summary['checks_run']} "
            f"info={reconcile_summary['info']} "
            f"warn={reconcile_summary['warn']} "
            f"fail={reconcile_summary['fail']} "
            f"status={reconcile_summary['status']}"
        )
    print("SYNC_ALL FAILED" if hard_failure else "SYNC_ALL OK")
    return 1 if hard_failure else 0


if __name__ == "__main__":
    sys.exit(main())
