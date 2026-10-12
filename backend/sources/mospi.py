"""MoSPI macro indicators via the data.gov.in OGD API (P4-B, roadmap 4.2).

Fetches headline Indian macro series (CPI inflation, WPI inflation, IIP, GDP
growth) from the Open Government Data platform:

    GET https://api.data.gov.in/resource/{resource_id}
        ?api-key={OGD_API_KEY}&format=json&limit=...

The response envelope is ``{"records": [...], "count": n, "total": n, ...}``
(OGD standard); each record is a flat dict whose period/value field names
vary by dataset, so the field mapping lives in db_config.json ->
sources.ogd.resources (single source of truth — no resource IDs or field
names hardcoded here).

Coverage notes (documented 2026-10, never worked around silently):
  * cpi_inflation / wpi_inflation have community-verified OGD resource IDs
    (see the per-series ``note`` in db_config.json); the field-name mapping
    is best-effort and rows lacking the configured fields are dropped —
    never defaulted.
  * iip and gdp_growth have NO live OGD resource (searched: only stale
    one-off tables; MoSPI publishes them via eSankhyiki / PIB PDFs). Their
    config entries carry ``resource_id: ""`` and are skipped with a log
    line — per SPEC, unsynced beats fabricated.
  * The API key comes from settings.ogd_api_key (env OGD_API_KEY); when
    unset the whole sync is skipped cleanly with a log line.
  * Live reachability of api.data.gov.in could not be verified from the
    build environment (restricted egress); tests run on recorded fixtures.

Period semantics (SPEC): monthly series -> "YYYY-MM", quarterly -> "YYYY-Qn".
"""

from __future__ import annotations

import re
from typing import Any

import requests
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential_jitter

from ..db import load_config
from ..ingestion import ingestion_run
from ..logging_config import get_logger
from ..macro import upsert_observation
from ..providers.ratelimit import TokenBucket
from ..settings import get_settings

logger = get_logger("sources.mospi")

DEFAULT_REQUESTS_PER_MINUTE = 30
REQUEST_TIMEOUT = 30  # seconds
JOB = "mospi_macro"

_HEADERS = {
    "User-Agent": ("BazzarTerminal/1.6 (+https://github.com/Tech-ka-14/bazzar; macro data sync)"),
    "Accept": "application/json",
}

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}

_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


class SourceError(Exception):
    """Fatal error talking to a data source (after retries)."""


def ogd_config() -> dict[str, Any]:
    """The ``sources.ogd`` block of db_config.json."""
    return load_config()["sources"]["ogd"]


def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, (requests.RequestException, ConnectionError, TimeoutError))


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    """Find the record list inside an OGD payload (``{"records": [...]}``,
    tolerant of a bare list or ``{"data"/"result": [...]}`` containers)."""
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        for key in ("records", "data", "result", "rows"):
            value = payload.get(key)
            if isinstance(value, list):
                return [r for r in value if isinstance(r, dict)]
    return []


def _field(row: dict[str, Any], candidates: str | list[str]) -> Any:
    """First non-None cell among ``candidates`` (exact key, then casefold)."""
    if isinstance(candidates, str):
        candidates = [candidates]
    for key in candidates:
        if key in row and row[key] is not None:
            return row[key]
    folded = {str(k).casefold(): v for k, v in row.items() if v is not None}
    for key in candidates:
        if key.casefold() in folded:
            return folded[key.casefold()]
    return None


def parse_period(raw: Any, period_format: str) -> str | None:
    """Normalise one OGD period label, or None when unparseable.

    monthly ("YYYY-MM"):   "2025-01", "2025-01-15" (truncated), "01/2025",
                           "01-2025", "Jan 2025", "January-2025", "2025/01".
    quarterly ("YYYY-Qn"): "2025-Q1", "Q1 2025", "Q1 2024-25" (Indian fiscal
                           convention: Q1 FY2024-25 = Apr–Jun 2024, labelled
                           by its starting calendar year -> "2024-Q1").
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if period_format == "monthly":
        m = re.fullmatch(r"(\d{4})[-/](\d{1,2})(?:-\d{1,2})?", text)
        if m and 1 <= int(m.group(2)) <= 12:
            return f"{m.group(1)}-{int(m.group(2)):02d}"
        m = re.fullmatch(r"(\d{1,2})[-/](\d{4})", text)
        if m and 1 <= int(m.group(1)) <= 12:
            return f"{m.group(2)}-{int(m.group(1)):02d}"
        m = re.fullmatch(r"([A-Za-z]{3,9})[\s\-](\d{4})", text)
        if m and m.group(1)[:3].lower() in _MONTHS:
            return f"{m.group(2)}-{_MONTHS[m.group(1)[:3].lower()]:02d}"
        m = re.fullmatch(r"(\d{4})[\s\-]([A-Za-z]{3,9})", text)
        if m and m.group(2)[:3].lower() in _MONTHS:
            return f"{m.group(1)}-{_MONTHS[m.group(2)[:3].lower()]:02d}"
        return None
    if period_format == "quarterly":
        m = re.fullmatch(r"(\d{4})[-\s]?[Qq]([1-4])", text)
        if m:
            return f"{m.group(1)}-Q{m.group(2)}"
        m = re.fullmatch(r"[Qq]([1-4])\s*(?:FY\s*)?(\d{4})(?:-(\d{2,4}))?", text)
        if m:
            return f"{m.group(2)}-Q{m.group(1)}"
        return None
    raise ValueError(f"unknown period_format '{period_format}'")


def _as_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-", "NA", "N/A"):
            return None
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def parse_ogd_records(
    payload: Any,
    *,
    value_field: str | list[str],
    period_field: str | list[str],
    period_format: str,
) -> list[dict[str, Any]]:
    """Pure parser: OGD payload -> [{"period", "value"}] observations.

    Rows with an unparseable period or a missing/blank value are dropped
    (never defaulted). Output is sorted by period, de-duplicated (last wins).
    """
    out: dict[str, float] = {}
    for row in _extract_records(payload):
        period = parse_period(_field(row, period_field), period_format)
        value = _as_float(_field(row, value_field))
        if period is None or value is None:
            continue
        out[period] = value
    return [{"period": p, "value": out[p]} for p in sorted(out)]


class MospiSource:
    """HTTP client for the data.gov.in OGD API (injectable session for tests)."""

    name = "mospi_ogd"

    def __init__(
        self,
        session: Any | None = None,
        *,
        requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE,
        config: dict[str, Any] | None = None,
        api_key: str | None = None,
    ):
        self._session = session or requests.Session()
        self._session.headers.update(_HEADERS)
        self._bucket = TokenBucket(requests_per_minute, jitter_seconds=0.1)
        self.config = config or ogd_config()
        self.api_key = api_key

    # --- HTTP plumbing ------------------------------------------------------

    def _resource_url(self, resource_id: str) -> str:
        base = self.config["base_url"].rstrip("/")
        return f"{base}{self.config.get('resource_path', '/resource')}/{resource_id}"

    def _get(self, resource_id: str) -> Any:
        """GET one OGD resource with retry/backoff on 429/5xx and network
        errors; returns the raw response object."""

        def _do() -> Any:
            self._bucket.acquire()
            resp = self._session.get(
                self._resource_url(resource_id),
                params={
                    "api-key": self.api_key,
                    "format": self.config.get("format", "json"),
                    "limit": int(self.config.get("limit", 100)),
                },
                timeout=REQUEST_TIMEOUT,
            )
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

    @staticmethod
    def _decode_payload(resp: Any) -> Any:
        try:
            return resp.json()
        except ValueError as exc:
            raise SourceError(f"OGD response is not JSON: {exc}") from exc

    # --- data access ----------------------------------------------------------

    def series_entry(self, local_key: str) -> dict[str, Any] | None:
        """Config entry for a macro series key, or None."""
        entry = self.config.get("resources", {}).get(local_key)
        return entry

    def fetch_series(self, local_key: str) -> list[dict[str, Any]]:
        """Fetch one configured series -> [{"period", "value"}] observations.

        Raises KeyError for an unconfigured key and SourceError when the
        config entry carries no resource id (documented gap — the caller
        skips; nothing is fabricated) or no API key is available.
        """
        entry = self.series_entry(local_key)
        if entry is None:
            raise KeyError(f"no sources.ogd.resources config entry for series '{local_key}'")
        resource_id = (entry.get("resource_id") or "").strip()
        if not resource_id:
            raise SourceError(
                f"series '{local_key}' has no OGD resource configured"
                " (see the note in db_config.json -> sources.ogd.resources)"
            )
        if not self.api_key:
            raise SourceError("OGD_API_KEY not set — cannot fetch OGD resources")
        resp = self._get(resource_id)
        return parse_ogd_records(
            self._decode_payload(resp),
            value_field=entry["value_field"],
            period_field=entry["period_field"],
            period_format=entry["period_format"],
        )


def sync(con, source: MospiSource | None = None) -> dict[str, Any]:
    """Fetch all configured MoSPI/OGD series into macro_observations.

    Returns a summary dict {"synced": {key: n}, "skipped": [keys]}. The
    whole sync is skipped cleanly when OGD_API_KEY is unset; per-series
    failures (including series with no OGD resource) are logged, counted
    and recorded on the ingestion run (status=partial) — the remaining
    series still sync.
    """
    settings = get_settings()
    summary: dict[str, Any] = {"synced": {}, "skipped": []}
    if source is None:
        source = MospiSource(api_key=settings.ogd_api_key)
    if not source.api_key:
        logger.warning(
            "OGD_API_KEY not set — skipping MoSPI/OGD macro sync (never fabricate);"
            " get a free key at https://data.gov.in/user"
        )
        summary["skipped"] = list(source.config.get("resources", {}))
        return summary
    errors: list[str] = []
    with ingestion_run(con, JOB) as run:
        for key, _entry in source.config.get("resources", {}).items():
            try:
                obs = source.fetch_series(key)
            except (SourceError, KeyError, requests.RequestException) as exc:
                logger.warning("ogd series fetch failed", series=key, error=str(exc))
                errors.append(f"{key}: {exc}")
                summary["skipped"].append(key)
                continue
            for o in obs:
                upsert_observation(con, key, o["period"], o["value"])
                run.rows_written += 1
            summary["synced"][key] = len(obs)
        if errors:
            run.error = "; ".join(errors)[:1000]
    return summary
