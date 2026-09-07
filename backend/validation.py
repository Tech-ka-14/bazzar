"""Write-path validation for market data.

Every external write goes through these validators before touching the
database. Invalid rows are NEVER silently dropped and NEVER crash a run:
they are quarantined into the ``data_rejects`` table (migration 0002) with
the job name, target table, full payload (JSON) and a human-readable reason.

OHLCV bar rules (daily bars, equities and indices):
  * all required fields present and non-null
  * prices strictly positive
  * high >= low
  * low <= open <= high and low <= close <= high
  * volume >= 0 when present (indices carry no volume)
  * date not in the future
  * no duplicate (symbol, exchange, date) inside one batch
  * date must be a known trading day when it falls inside the seeded
    trading-calendar coverage window (outside coverage: not checked)
"""

from __future__ import annotations

import datetime as dt
import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import duckdb

from .calendar import DEFAULT_EXCHANGE, holiday_name, is_trading_day

_PRICE_FIELDS = ("open", "high", "low", "close")


@dataclass(frozen=True)
class Reject:
    """One row that failed validation, with the reason."""

    payload: dict[str, Any]
    reason: str


def _parse_date(value: Any) -> dt.date | None:
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def validate_bars(
    bars: Iterable[dict[str, Any]],
    *,
    symbol: str,
    exchange: str,
    con: duckdb.DuckDBPyConnection | None = None,
    volume_optional: bool = False,
    calendar_exchange: str = DEFAULT_EXCHANGE,
    today: dt.date | None = None,
) -> tuple[list[dict[str, Any]], list[Reject]]:
    """Split a batch of OHLCV bars into (valid, rejects).

    ``con`` enables the trading-calendar check; without it only structural
    rules are applied. ``today`` is injectable for tests.
    """
    today = today or dt.date.today()
    valid: list[dict[str, Any]] = []
    rejects: list[Reject] = []
    seen_dates: set[dt.date] = set()

    for bar in bars:
        reason = _check_bar(
            bar,
            volume_optional=volume_optional,
            today=today,
            seen_dates=seen_dates,
            con=con,
            calendar_exchange=calendar_exchange,
        )
        if reason is None:
            seen_dates.add(_parse_date(bar["date"]))  # type: ignore[arg-type]
            valid.append(bar)
        else:
            rejects.append(
                Reject(payload={"symbol": symbol, "exchange": exchange, **bar}, reason=reason)
            )
    return valid, rejects


def _check_bar(
    bar: dict[str, Any],
    *,
    volume_optional: bool,
    today: dt.date,
    seen_dates: set[dt.date],
    con: duckdb.DuckDBPyConnection | None,
    calendar_exchange: str,
) -> str | None:
    required = ["date", *_PRICE_FIELDS] + ([] if volume_optional else ["volume"])
    for field in required:
        if field not in bar or bar[field] is None:
            return f"missing field: {field}"

    day = _parse_date(bar["date"])
    if day is None:
        return f"unparseable date: {bar['date']!r}"
    if day > today:
        return f"future date: {day.isoformat()}"
    if day in seen_dates:
        return f"duplicate date in batch: {day.isoformat()}"

    try:
        open_, high, low, close = (float(bar[f]) for f in _PRICE_FIELDS)
    except (TypeError, ValueError):
        return "non-numeric price field"
    if min(open_, high, low, close) <= 0:
        return "non-positive price"
    if high < low:
        return f"high ({high}) < low ({low})"
    if not low <= open_ <= high:
        return f"open ({open_}) outside [low, high] = [{low}, {high}]"
    if not low <= close <= high:
        return f"close ({close}) outside [low, high] = [{low}, {high}]"

    volume = bar.get("volume")
    if volume is not None:
        try:
            if int(volume) < 0:
                return f"negative volume: {volume}"
        except (TypeError, ValueError):
            return f"non-numeric volume: {volume!r}"

    if con is not None:
        trading = is_trading_day(con, day, calendar_exchange)
        if trading is False:
            name = holiday_name(con, day, calendar_exchange) or "non-trading day"
            return f"non-trading day: {day.isoformat()} ({name})"
    return None


def quarantine_rejects(
    con: duckdb.DuckDBPyConnection,
    *,
    job: str,
    table_name: str,
    rejects: Iterable[Reject],
) -> int:
    """Write rejected rows to data_rejects. Returns the number quarantined."""
    rejects = list(rejects)
    if not rejects:
        return 0
    con.executemany(
        "INSERT INTO data_rejects (job, table_name, payload, reason) VALUES (?, ?, ?, ?)",
        [(job, table_name, json.dumps(r.payload, default=str), r.reason) for r in rejects],
    )
    return len(rejects)


def upsert_daily_ohlcv(
    con: duckdb.DuckDBPyConnection,
    *,
    job: str,
    symbol: str,
    exchange: str,
    bars: list[dict[str, Any]],
) -> tuple[int, int]:
    """Validate then idempotently upsert equity daily bars.

    Returns (rows_written, rows_rejected). Rejects are quarantined.
    """
    valid, rejects = validate_bars(bars, symbol=symbol, exchange=exchange, con=con)
    quarantine_rejects(con, job=job, table_name="daily_ohlcv", rejects=rejects)
    if valid:
        con.executemany(
            "INSERT INTO daily_ohlcv (symbol, exchange, date, open, high, low, close, volume)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            " ON CONFLICT (symbol, exchange, date) DO UPDATE SET open = excluded.open,"
            " high = excluded.high, low = excluded.low, close = excluded.close,"
            " volume = excluded.volume",
            [
                (
                    symbol,
                    exchange,
                    b["date"],
                    b["open"],
                    b["high"],
                    b["low"],
                    b["close"],
                    b["volume"],
                )
                for b in valid
            ],
        )
    return len(valid), len(rejects)


def upsert_index_daily(
    con: duckdb.DuckDBPyConnection,
    *,
    job: str,
    symbol: str,
    exchange: str,
    bars: list[dict[str, Any]],
) -> tuple[int, int]:
    """Validate then idempotently upsert index daily bars (no volume column)."""
    valid, rejects = validate_bars(
        bars, symbol=symbol, exchange=exchange, con=con, volume_optional=True
    )
    quarantine_rejects(con, job=job, table_name="index_daily", rejects=rejects)
    if valid:
        con.executemany(
            "INSERT INTO index_daily (symbol, date, open, high, low, close)"
            " VALUES (?, ?, ?, ?, ?, ?)"
            " ON CONFLICT (symbol, date) DO UPDATE SET open = excluded.open,"
            " high = excluded.high, low = excluded.low, close = excluded.close",
            [(symbol, b["date"], b["open"], b["high"], b["low"], b["close"]) for b in valid],
        )
    return len(valid), len(rejects)
