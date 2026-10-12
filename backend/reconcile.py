"""Data-quality reconciliation checks (P4-C, roadmap 4.5).

Every check writes append-only audit rows into the ``data_quality`` table
(migration 0004); ``run_all`` wraps the whole pass in an
``ingestion_run(con, "reconcile")`` so the ops audit trail records when
checks ran and whether any fail-severity findings occurred (status=partial).

Hard rules honoured here (SPEC):
  * never fabricate — when one side of a comparison has no data the check
    records an info row ("no data to compare"), never an assumed value;
  * every finding carries the measured/expected values in ``details``;
  * check crashes become fail rows instead of aborting the remaining checks.

Checks:
  * ``check_kite_vs_bhavcopy`` — stored NSE closes (daily_ohlcv, written by
    the Kite/bhavcopy fetchers) vs the official NSE bhavcopy for the latest
    stored trading day. The provider is injectable for tests; when no
    provider/credentials are available the check records an info row.
  * ``check_macro_freshness`` — per macro_series key, lag between the latest
    stored period and the expected period for the series' ``frequency``
    (db_config.json -> macro_indicators). Never-synced series -> info.
  * ``check_benchmark_freshness`` — per benchmark_series key, age of the
    latest observation vs the group's expected cadence.

CLI:
    python3 -m backend.reconcile            # run all checks, print summary
Exit code is 1 when any fail-severity finding was recorded, else 0.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from typing import Any

import duckdb

from .db import get_connection, initialize_database, load_config
from .ingestion import ingestion_run
from .logging_config import get_logger

logger = get_logger("reconcile")

JOB = "reconcile"

SEVERITY_INFO = "info"
SEVERITY_WARN = "warn"
SEVERITY_FAIL = "fail"
SEVERITIES = (SEVERITY_INFO, SEVERITY_WARN, SEVERITY_FAIL)

CHECK_KITE_BHAVCOPY = "kite_vs_bhavcopy"
CHECK_MACRO_FRESHNESS = "macro_freshness"
CHECK_BENCHMARK_FRESHNESS = "benchmark_freshness"

# Freshness tolerances (documented constants — there is no per-series
# override in db_config.json yet). A series is FRESH while its lag stays
# within the tolerance, WARN when stale (lag > tolerance) and FAIL when very
# stale (lag > 2x tolerance). Lags are measured in the series' own period
# unit: months for monthly, quarters for quarterly, days for weekly /
# fortnightly. Frequencies without an entry (e.g. "event-driven" policy
# rates) have no checkable cadence and are reported as info only.
#
# The nominal publication lag is ~1-2 months for monthly Indian macro series
# and ~1-2 quarters for quarterly ones, so tolerance=2 means "expected by
# ~1-2 periods back".
MACRO_TOLERANCE = {
    "monthly": ("months", 2),
    "quarterly": ("quarters", 2),
    "weekly": ("days", 14),
    "fortnightly": ("days", 35),
}

# Benchmark groups and the maximum accepted age (calendar days) of the latest
# observation before warn (fail beyond 2x). Daily-published groups
# (rbi_gsec, us_treasury_10y, fii_dii) expect a row within ~7 calendar days
# (weekends + exchange holidays); monthly-published groups (repo_rates: RBI
# key rates + FRED FEDFUNDS) get 45 days. Groups without an entry (sgb — no
# automated source yet) are reported as info only.
BENCHMARK_MAX_AGE_DAYS = {
    "rbi_gsec": 7,
    "us_treasury_10y": 7,
    "fii_dii": 7,
    "repo_rates": 45,
}

# The kite-vs-bhavcopy check anchors on the latest stored NSE bar and only
# runs when that bar is recent: 10 calendar days ≈ the last 5 trading days
# (weekends + holidays). Older stores have nothing current to reconcile.
RECENT_BAR_MAX_AGE_DAYS = 10


def record_check(
    con: duckdb.DuckDBPyConnection,
    check_name: str,
    target: str,
    severity: str,
    message: str,
    *,
    period: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append one data_quality audit row and return it as a dict."""
    if severity not in SEVERITIES:
        raise ValueError(f"unknown severity '{severity}' (expected one of {SEVERITIES})")
    payload = json.dumps(details, sort_keys=True, default=str) if details is not None else None
    con.execute(
        "INSERT INTO data_quality (check_name, target, period, severity, message, details)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (check_name, target, period, severity, message, payload),
    )
    return {
        "check_name": check_name,
        "target": target,
        "period": period,
        "severity": severity,
        "message": message,
        "details": details,
    }


# --- kite vs bhavcopy --------------------------------------------------------


def _default_bhavcopy_provider() -> Any:
    from .providers.nse_bhavcopy import NseBhavcopyProvider

    return NseBhavcopyProvider()


def check_kite_vs_bhavcopy(
    con: duckdb.DuckDBPyConnection,
    provider: Any | None = None,
    sample: int = 10,
    tolerance_pct: float = 0.5,
) -> list[dict[str, Any]]:
    """Compare stored NSE closes against the official NSE bhavcopy.

    Picks up to ``sample`` random NSE symbols with a bar on the latest stored
    trading day (only when that day is recent — see RECENT_BAR_MAX_AGE_DAYS),
    fetches the bhavcopy rows for that date via the provider's parse path,
    and flags close differences beyond ``tolerance_pct`` percent (warn;
    beyond 2x -> fail). Missing data on either side is an info row, never a
    fabricated comparison.
    """
    rows: list[dict[str, Any]] = []

    def rec(target: str, severity: str, message: str, **kwargs: Any) -> None:
        rows.append(record_check(con, CHECK_KITE_BHAVCOPY, target, severity, message, **kwargs))

    latest_row = con.execute("SELECT MAX(date) FROM daily_ohlcv WHERE exchange = 'NSE'").fetchone()
    latest = latest_row[0] if latest_row else None
    if latest is None:
        rec("-", SEVERITY_INFO, "no NSE bars stored — nothing to reconcile")
        return rows
    latest_day = latest if isinstance(latest, dt.date) else dt.date.fromisoformat(str(latest)[:10])
    age_days = (dt.date.today() - latest_day).days
    if age_days > RECENT_BAR_MAX_AGE_DAYS:
        rec(
            "-",
            SEVERITY_INFO,
            f"latest stored NSE bar is {latest_day} ({age_days}d old) — outside the"
            f" recent {RECENT_BAR_MAX_AGE_DAYS}d window, nothing current to reconcile",
            period=latest_day.isoformat(),
        )
        return rows

    if provider is None:
        try:
            provider = _default_bhavcopy_provider()
        except Exception as exc:  # missing deps/credentials — not a data issue
            rec("-", SEVERITY_INFO, f"bhavcopy provider unavailable: {exc}")
            return rows

    try:
        bhav_rows = provider.fetch_day(latest_day)
    except Exception as exc:  # offline / 5xx after retries — never fatal
        rec(
            "-",
            SEVERITY_INFO,
            f"bhavcopy fetch for {latest_day} unavailable ({exc}) — no data to compare",
            period=latest_day.isoformat(),
        )
        return rows
    if not bhav_rows:
        rec(
            "-",
            SEVERITY_INFO,
            f"no bhavcopy rows for {latest_day} (holiday or unpublished) — no data to compare",
            period=latest_day.isoformat(),
        )
        return rows
    bhav_close = {
        r["symbol"]: r["close"] for r in bhav_rows if r.get("symbol") and r.get("close") is not None
    }

    sampled = con.execute(
        "SELECT symbol, close FROM daily_ohlcv WHERE exchange = 'NSE' AND date = ?"
        " ORDER BY random() LIMIT ?",
        (latest_day, max(0, int(sample))),
    ).fetchall()
    if not sampled:
        rec("-", SEVERITY_INFO, f"no stored NSE bars on {latest_day} — no data to compare")
        return rows

    for symbol, close in sampled:
        period = latest_day.isoformat()
        if close is None:
            rec(symbol, SEVERITY_INFO, "stored close is null — no data to compare", period=period)
            continue
        other = bhav_close.get(symbol)
        if other is None:
            rec(
                symbol,
                SEVERITY_INFO,
                f"symbol absent from the {latest_day} bhavcopy — no data to compare",
                period=period,
            )
            continue
        diff_pct = abs(float(close) - other) / other * 100 if other else 0.0
        details = {
            "stored_close": float(close),
            "bhavcopy_close": other,
            "diff_pct": round(diff_pct, 4),
            "tolerance_pct": tolerance_pct,
        }
        if diff_pct <= tolerance_pct:
            rec(
                symbol,
                SEVERITY_INFO,
                f"close matches bhavcopy (diff {diff_pct:.4f}% within {tolerance_pct}%)",
                period=period,
                details=details,
            )
        elif diff_pct <= 2 * tolerance_pct:
            rec(
                symbol,
                SEVERITY_WARN,
                f"close differs from bhavcopy by {diff_pct:.4f}% (tolerance {tolerance_pct}%)",
                period=period,
                details=details,
            )
        else:
            rec(
                symbol,
                SEVERITY_FAIL,
                f"close differs from bhavcopy by {diff_pct:.4f}% (>2x tolerance {tolerance_pct}%)",
                period=period,
                details=details,
            )
    return rows


# --- macro freshness -----------------------------------------------------------


def _period_lag(period: str, frequency: str, today: dt.date) -> float | None:
    """Lag between a stored period label and today, in the frequency's unit.

    monthly -> whole months ("YYYY-MM"); quarterly -> whole quarters
    ("YYYY-Qn"); weekly/fortnightly -> days ("YYYY-MM-DD" or "YYYY-MM",
    day defaults to the 1st). Returns None when the label is unparseable —
    the caller records an info row instead of guessing.
    """
    text = str(period).strip()
    if frequency == "quarterly":
        m = re.fullmatch(r"(\d{4})-?[Qq]([1-4])", text)
        if not m:
            return None
        year, quarter = int(m.group(1)), int(m.group(2))
        current_quarter = (today.month - 1) // 3 + 1
        return float((today.year * 4 + current_quarter) - (year * 4 + quarter))
    m = re.fullmatch(r"(\d{4})-(\d{1,2})(?:-(\d{1,2}))?", text)
    if not m:
        return None
    year, month = int(m.group(1)), int(m.group(2))
    try:
        day = dt.date(year, month, int(m.group(3) or 1))
    except ValueError:
        return None
    if frequency == "monthly":
        return float((today.year * 12 + today.month) - (year * 12 + month))
    return float((today - day).days)


def check_macro_freshness(con: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    """Freshness of every macro_series key vs its configured frequency.

    Series with zero observations -> info "never synced" (SPEC: unsynced
    beats fabricated). Stale (lag > tolerance) -> warn; very stale
    (lag > 2x tolerance) -> fail.
    """
    rows: list[dict[str, Any]] = []
    today = dt.date.today()
    series = con.execute("SELECT key, frequency FROM macro_series ORDER BY key").fetchall()
    for key, frequency in series:
        period_row = con.execute(
            "SELECT MAX(period) FROM macro_observations WHERE series_key = ?", (key,)
        ).fetchone()
        latest_period = period_row[0] if period_row else None
        if latest_period is None:
            rows.append(
                record_check(
                    con, CHECK_MACRO_FRESHNESS, key, SEVERITY_INFO, "never synced — no observations"
                )
            )
            continue
        freq = (frequency or "").strip().lower()
        tolerance = MACRO_TOLERANCE.get(freq)
        if tolerance is None:
            rows.append(
                record_check(
                    con,
                    CHECK_MACRO_FRESHNESS,
                    key,
                    SEVERITY_INFO,
                    f"frequency '{frequency}' has no cadence expectation — freshness not checked",
                    period=str(latest_period),
                )
            )
            continue
        unit, max_lag = tolerance
        lag = _period_lag(str(latest_period), freq, today)
        if lag is None:
            rows.append(
                record_check(
                    con,
                    CHECK_MACRO_FRESHNESS,
                    key,
                    SEVERITY_INFO,
                    f"latest period '{latest_period}' is not a parseable {freq} period —"
                    " freshness not checked",
                    period=str(latest_period),
                )
            )
            continue
        details = {
            "latest_period": str(latest_period),
            "frequency": freq,
            "lag": lag,
            "lag_unit": unit,
            "tolerance": max_lag,
        }
        if lag <= max_lag:
            rows.append(
                record_check(
                    con,
                    CHECK_MACRO_FRESHNESS,
                    key,
                    SEVERITY_INFO,
                    f"fresh (latest period {latest_period}, lag {lag:g} {unit})",
                    period=str(latest_period),
                    details=details,
                )
            )
        elif lag <= 2 * max_lag:
            rows.append(
                record_check(
                    con,
                    CHECK_MACRO_FRESHNESS,
                    key,
                    SEVERITY_WARN,
                    f"stale: latest period {latest_period} lags {lag:g} {unit}"
                    f" (tolerance {max_lag})",
                    period=str(latest_period),
                    details=details,
                )
            )
        else:
            rows.append(
                record_check(
                    con,
                    CHECK_MACRO_FRESHNESS,
                    key,
                    SEVERITY_FAIL,
                    f"very stale: latest period {latest_period} lags {lag:g} {unit}"
                    f" (>2x tolerance {max_lag})",
                    period=str(latest_period),
                    details=details,
                )
            )
    return rows


# --- benchmark freshness -------------------------------------------------------


def check_benchmark_freshness(con: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    """Freshness of every benchmark_series key vs its group's expected cadence.

    Daily groups (rbi_gsec, us_treasury_10y, fii_dii) expect an observation
    within BENCHMARK_MAX_AGE_DAYS calendar days; monthly groups (repo_rates)
    get a longer window. Series with zero observations -> info "never synced".
    """
    rows: list[dict[str, Any]] = []
    today = dt.date.today()
    for group in load_config()["benchmarks"]:
        max_age = BENCHMARK_MAX_AGE_DAYS.get(group["key"])
        for series in group["series"]:
            key = series["key"]
            date_row = con.execute(
                "SELECT MAX(date) FROM benchmark_observations WHERE series_key = ?", (key,)
            ).fetchone()
            latest = date_row[0] if date_row else None
            if max_age is None:
                rows.append(
                    record_check(
                        con,
                        CHECK_BENCHMARK_FRESHNESS,
                        key,
                        SEVERITY_INFO,
                        f"benchmark group '{group['key']}' has no freshness expectation"
                        " configured — not checked",
                        period=str(latest)[:10] if latest else None,
                    )
                )
                continue
            if latest is None:
                rows.append(
                    record_check(
                        con,
                        CHECK_BENCHMARK_FRESHNESS,
                        key,
                        SEVERITY_INFO,
                        "never synced — no observations",
                    )
                )
                continue
            latest_day = (
                latest if isinstance(latest, dt.date) else dt.date.fromisoformat(str(latest)[:10])
            )
            age = (today - latest_day).days
            details = {
                "latest_date": latest_day.isoformat(),
                "age_days": age,
                "max_age_days": max_age,
                "group": group["key"],
            }
            if age <= max_age:
                rows.append(
                    record_check(
                        con,
                        CHECK_BENCHMARK_FRESHNESS,
                        key,
                        SEVERITY_INFO,
                        f"fresh (latest {latest_day}, {age}d old)",
                        period=latest_day.isoformat(),
                        details=details,
                    )
                )
            elif age <= 2 * max_age:
                rows.append(
                    record_check(
                        con,
                        CHECK_BENCHMARK_FRESHNESS,
                        key,
                        SEVERITY_WARN,
                        f"stale: latest observation {latest_day} is {age}d old (max {max_age}d)",
                        period=latest_day.isoformat(),
                        details=details,
                    )
                )
            else:
                rows.append(
                    record_check(
                        con,
                        CHECK_BENCHMARK_FRESHNESS,
                        key,
                        SEVERITY_FAIL,
                        f"very stale: latest observation {latest_day} is {age}d old"
                        f" (>2x max {max_age}d)",
                        period=latest_day.isoformat(),
                        details=details,
                    )
                )
    return rows


# --- runner --------------------------------------------------------------------


def run_all(
    con: duckdb.DuckDBPyConnection,
    provider: Any | None = None,
    *,
    sample: int = 10,
    tolerance_pct: float = 0.5,
) -> dict[str, Any]:
    """Run every data-quality check inside one ``ingestion_run(con, "reconcile")``.

    Returns a summary dict: {checks_run, info, warn, fail, status, run_id,
    rows}. ``status`` is "green" (no warn/fail), "amber" (warns only) or
    "red" (any fail); any fail-severity finding also marks the ingestion run
    partial. A crashing check is recorded as a fail row — the remaining
    checks still run.
    """
    checks = (
        (CHECK_KITE_BHAVCOPY, lambda: check_kite_vs_bhavcopy(con, provider, sample, tolerance_pct)),
        (CHECK_MACRO_FRESHNESS, lambda: check_macro_freshness(con)),
        (CHECK_BENCHMARK_FRESHNESS, lambda: check_benchmark_freshness(con)),
    )
    counts = {SEVERITY_INFO: 0, SEVERITY_WARN: 0, SEVERITY_FAIL: 0}
    all_rows: list[dict[str, Any]] = []
    checks_run = 0
    with ingestion_run(con, JOB) as run:
        for name, check in checks:
            try:
                found = check()
            except Exception as exc:  # a crashing check is itself a finding
                logger.error("data-quality check crashed", check=name, error=str(exc))
                found = [
                    record_check(
                        con, name, "-", SEVERITY_FAIL, f"check crashed: {type(exc).__name__}: {exc}"
                    )
                ]
            checks_run += 1
            for row in found:
                counts[row["severity"]] += 1
                run.rows_written += 1
            all_rows.extend(found)
        if counts[SEVERITY_FAIL]:
            run.error = f"{counts[SEVERITY_FAIL]} fail-severity data-quality finding(s)"
        run_id = run.run_id
    status = "green"
    if counts[SEVERITY_WARN]:
        status = "amber"
    if counts[SEVERITY_FAIL]:
        status = "red"
    summary: dict[str, Any] = {
        "checks_run": checks_run,
        **counts,
        "status": status,
        "run_id": run_id,
        "rows": all_rows,
    }
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m backend.reconcile",
        description="Run the data-quality reconciliation checks (P4-C) and print"
        " a summary. Exit code 1 when any fail-severity finding is recorded.",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=10,
        help="max symbols sampled for the kite-vs-bhavcopy check (default 10)",
    )
    parser.add_argument(
        "--tolerance-pct",
        type=float,
        default=0.5,
        help="close-price tolerance in percent for kite-vs-bhavcopy (default 0.5)",
    )
    args = parser.parse_args(argv)

    initialize_database()
    con = get_connection()
    try:
        summary = run_all(con, sample=args.sample, tolerance_pct=args.tolerance_pct)
    finally:
        con.close()

    for row in summary["rows"]:
        if row["severity"] == SEVERITY_INFO:
            continue  # info rows are audit noise on the console
        period = f" [{row['period']}]" if row.get("period") else ""
        print(
            f"{row['severity'].upper():5} {row['check_name']}:{row['target']}{period}"
            f" — {row['message']}"
        )
    print(
        f"reconcile: {summary['checks_run']} checks run — "
        f"info={summary['info']} warn={summary['warn']} fail={summary['fail']}"
        f" status={summary['status']}"
    )
    return 1 if summary["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
