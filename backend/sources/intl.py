"""International benchmark source fetcher (P4-A, roadmap 4.4).

Fetches the international benchmark series from db_config.json -> benchmarks:

  * ``us_10y`` — US Treasury daily par yield curve rates, official CSV
    endpoint (no key required):

        https://home.treasury.gov/resource-center/data-chart-center/
        interest-rates/daily-treasury-rates.csv/{year}/all
        ?type=daily_treasury_yield_curve&field_tdr_date_value={year}&page&_format=csv

    The CSV header changed when Treasury moved to the "Daily Treasury Par
    Yield Curve Rates" format: the 10-year column is ``BC_10YEAR`` in the
    current format and ``10 Yr`` in the legacy format. The parser accepts
    either (and the date column is ``Date``, MM/DD/YYYY).

  * ``us_fed_funds`` — FRED series FEDFUNDS (effective federal funds rate,
    monthly, percent; observation date = first of month):

        https://api.stlouisfed.org/fred/series/observations
        ?series_id=FEDFUNDS&api_key=<key>&file_type=json

    Requires a free FRED API key (https://fred.stlouisfed.org/docs/api/api_key.html)
    via settings ``fred_api_key`` / env ``FRED_API_KEY``. When unset the
    series is SKIPPED with a log line — per SPEC, unsynced beats fabricated.

Series ids / endpoint parameters live in db_config.json -> sources
(single source of truth). The HTTP session is injectable for tests (no
network in CI); parser tests run offline against recorded fixtures.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
from typing import Any

import requests
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential_jitter

from ..benchmarks import upsert_benchmark_observation
from ..db import load_config
from ..ingestion import ingestion_run
from ..logging_config import get_logger
from ..providers.ratelimit import TokenBucket
from ..settings import get_settings
from .rbi import SourceError

logger = get_logger("sources.intl")

DEFAULT_REQUESTS_PER_MINUTE = 30
REQUEST_TIMEOUT = 30  # seconds
JOB = "intl_benchmarks"

_HEADERS = {
    "User-Agent": ("BazzarTerminal/1.6 (+https://github.com/Tech-ka-14/bazzar; benchmark sync)"),
    "Accept": "text/csv,application/json,*/*",
}

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}

# 10-year column names across the Treasury CSV formats (newest first).
US_10Y_COLUMNS = ("BC_10YEAR", "10 Yr")


def intl_config() -> dict[str, Any]:
    """The ``sources`` blocks for the international fetchers."""
    return load_config()["sources"]


def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, (requests.RequestException, ConnectionError, TimeoutError))


def _as_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-", "NA", "N/A", "."):
            return None
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def parse_treasury_csv(
    text: str,
    *,
    yield_columns: tuple[str, ...] = US_10Y_COLUMNS,
    date_column: str = "Date",
) -> list[dict[str, Any]]:
    """Pure parser: Treasury daily yield-curve CSV -> [{"date", "value"}].

    Tolerant of both column layouts (``BC_10YEAR`` new / ``10 Yr`` legacy);
    blank or non-numeric cells are dropped, never defaulted. Dates are the
    US-style MM/DD/YYYY used by home.treasury.gov. Output sorted by date,
    de-duplicated (last wins).
    """
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = reader.fieldnames or []
    # tolerate stray whitespace / BOM in headers
    header_map = {(name or "").strip().lstrip("﻿"): (name or "") for name in fieldnames}
    date_field = header_map.get(date_column)
    yield_field = next((header_map[c] for c in yield_columns if c in header_map), None)
    if date_field is None:
        raise SourceError(f"treasury CSV is missing the '{date_column}' column")
    if yield_field is None:
        raise SourceError(f"treasury CSV has none of the expected 10Y columns {yield_columns}")
    out: dict[str, float] = {}
    for row in reader:
        raw_date = (row.get(date_field) or "").strip()
        value = _as_float(row.get(yield_field))
        try:
            day = dt.datetime.strptime(raw_date, "%m/%d/%Y").date()
        except ValueError:
            try:
                day = dt.date.fromisoformat(raw_date)
            except ValueError:
                continue
        if value is None:
            continue
        out[day.isoformat()] = value
    return [{"date": d, "value": out[d]} for d in sorted(out)]


def parse_fred_observations(payload: Any) -> list[dict[str, Any]]:
    """Pure parser: FRED series/observations JSON -> [{"date", "value"}].

    FRED marks missing values with "." — those observations are dropped,
    never defaulted. Output sorted by date, de-duplicated (last wins).
    """
    if not isinstance(payload, dict):
        return []
    observations = payload.get("observations")
    if not isinstance(observations, list):
        return []
    out: dict[str, float] = {}
    for obs in observations:
        if not isinstance(obs, dict):
            continue
        raw_date = str(obs.get("date") or "").strip()
        value = _as_float(obs.get("value"))
        try:
            day = dt.date.fromisoformat(raw_date)
        except ValueError:
            continue
        if value is None:
            continue
        out[day.isoformat()] = value
    return [{"date": d, "value": out[d]} for d in sorted(out)]


class IntlSource:
    """HTTP client for the international benchmark sources (US Treasury, FRED)."""

    name = "intl_benchmarks"

    def __init__(
        self,
        session: Any | None = None,
        *,
        requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE,
        config: dict[str, Any] | None = None,
    ):
        self._session = session or requests.Session()
        self._session.headers.update(_HEADERS)
        self._bucket = TokenBucket(requests_per_minute, jitter_seconds=0.1)
        self.config = config or intl_config()

    # --- HTTP plumbing ------------------------------------------------------

    def _get(self, url: str, params: dict[str, Any] | None = None) -> Any:
        """GET with retry/backoff on 429/5xx and network errors."""

        def _do() -> Any:
            self._bucket.acquire()
            resp = self._session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code in _RETRYABLE_STATUS:
                resp.raise_for_status()  # triggers tenacity retry
            resp.raise_for_status()
            return resp

        for attempt in Retrying(
            retry=retry_if_exception(_is_retryable),
            stop=stop_after_attempt(4),
            wait=wait_exponential_jitter(initial=1, max=20),
            reraise=True,
        ):
            with attempt:
                return _do()
        raise SourceError("unreachable: retry loop exited without result")

    # --- data access ----------------------------------------------------------

    def fetch_us_10y(self, year: int) -> list[dict[str, Any]]:
        """Daily 10-year Treasury par yields for one calendar year."""
        cfg = self.config["us_treasury"]
        url = cfg["base_url_template"].format(year=year)
        resp = self._get(url)
        text = resp.text if hasattr(resp, "text") else resp.content.decode("utf-8-sig")
        return parse_treasury_csv(
            text,
            yield_columns=tuple(cfg.get("yield_columns", US_10Y_COLUMNS)),
            date_column=cfg.get("date_column", "Date"),
        )

    def fetch_fed_funds(self, api_key: str) -> list[dict[str, Any]]:
        """Monthly effective federal funds rate from FRED (date = 1st of month)."""
        cfg = self.config["fred"]
        resp = self._get(
            cfg["base_url"],
            params={
                "series_id": cfg["fred_series_id"],
                "api_key": api_key,
                "file_type": "json",
            },
        )
        try:
            payload = json.loads(resp.text if hasattr(resp, "text") else resp.content)
        except ValueError as exc:
            raise SourceError(f"FRED response is not JSON: {exc}") from exc
        if isinstance(payload, dict) and payload.get("error_message"):
            raise SourceError(f"FRED API error: {payload['error_message']}")
        return parse_fred_observations(payload)


def sync(con, source: IntlSource | None = None, *, year: int | None = None) -> dict[str, Any]:
    """Fetch international benchmarks into benchmark_observations.

    ``year`` selects the Treasury curve download year (default: current
    year). Returns {"us_10y": n, "us_fed_funds": n|None, "skipped": [...]}.
    FRED is skipped when no API key is configured — never fabricated.
    """
    source = source or IntlSource()
    if year is None:
        year = dt.date.today().year
    settings = get_settings()
    summary: dict[str, Any] = {"us_10y": 0, "us_fed_funds": None, "skipped": []}
    errors: list[str] = []
    with ingestion_run(con, JOB) as run:
        treasury_key = source.config["us_treasury"].get("series_key", "us_10y")
        try:
            obs = source.fetch_us_10y(year)
            for o in obs:
                upsert_benchmark_observation(con, treasury_key, o["date"], o["value"])
                run.rows_written += 1
            summary["us_10y"] = len(obs)
        except (SourceError, KeyError, requests.RequestException) as exc:
            logger.warning("us treasury fetch failed", error=str(exc))
            errors.append(f"{treasury_key}: {exc}")
            summary["skipped"].append(treasury_key)

        fred_key = source.config["fred"].get("series_key", "us_fed_funds")
        if not settings.fred_api_key:
            logger.warning(
                "FRED_API_KEY not set — skipping us_fed_funds (never fabricate);"
                " get a free key at https://fred.stlouisfed.org/docs/api/api_key.html"
            )
            summary["skipped"].append(fred_key)
        else:
            try:
                obs = source.fetch_fed_funds(settings.fred_api_key)
                for o in obs:
                    upsert_benchmark_observation(con, fred_key, o["date"], o["value"])
                    run.rows_written += 1
                summary["us_fed_funds"] = len(obs)
            except (SourceError, KeyError, requests.RequestException) as exc:
                logger.warning("fred fetch failed", error=str(exc))
                errors.append(f"{fred_key}: {exc}")
                summary["skipped"].append(fred_key)
        if errors:
            run.error = "; ".join(errors)[:1000]
    return summary
