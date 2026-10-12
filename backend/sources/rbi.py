"""RBI DBIE (Database on Indian Economy) source fetcher (P4-A, roadmap 4.1).

Fetches policy rates, G-Sec / T-Bill yields and forex reserves from the
Reserve Bank of India's statistics portal.

Endpoint shape (documented 2026-10; RBI publishes no official API docs — this
shape is verified from the portal's SPA behaviour as captured by the Reserve
Bank Innovation Hub's DBIE mirror project, docs/dbie-portal-anatomy.md):

  * Portal: https://data.rbi.org.in (the old dbie.rbi.org.in was retired on
    2024-06-21 and redirects here).
  * Everything flows through one JSON gateway:

        POST https://data.rbi.org.in/CIMS_Gateway_DBIE/GATEWAY/SERVICES/<service>
        headers: content-type:  application/json
                 channelkey:    key2          (guest channel, baked into the SPA)
                 datatype:      application/json
                 authorization: <bearer>      (see session bootstrap below)
        body:    {"body": { ...service parameters... }}

    Responses are HTML-entity-encoded JSON (``html.unescape`` before parsing).
  * Session bootstrap: POST ``security_generateSessionToken`` with
    ``{"body": {}}``; the guest bearer token is returned in the
    ``Authorization`` response header (valid ~30–60 min idle).
  * Time-series data service: ``dbie_getImpalaDQActionEnhanced``. Series are
    addressed by SDMX DSD codes — the ones used here (verified against the
    portal's public ``dbie_getSectorAction`` catalogue):
      YIELD_GOV_SEC_RN  G-Sec SGL yields, dim column mat_per_rn_description
                        = residual maturity in years ("5" / "10")
      YIELD_TB_RN       T-Bill SGL yields, dim mat_term_d_rn_description
                        ("15-91 days" / code 15TO91 for the 91-day bill)
      FR_EXG_RESV_RN    weekly forex reserves, dim typ_maj_fr_exc_res_rn_
                        description ("Foreign Exchange Reserves" / FER_TTL)
                        and unit_measure_description ("US dollar")
    Response rows carry the SDMX observation core (TIME_PERIOD, OBS_VALUE,
    UNIT_MULT, FREQ, ...) plus one description column per dimension.

  * KNOWN GAP (documented, never worked around silently): the SPA
    AES-256-CBC-encrypts the request fields of the data-query services with a
    static key baked into its JS bundle ("encrypted on the way in, plaintext
    out"). This module posts the documented plain body; if RBI enforces
    encryption on the wire the fetch fails loudly and ``sync`` records a
    failed/partial ingestion run — nothing is fabricated.
  * Policy rates (repo / reverse repo / CRR) are NOT part of the SDMX data
    query catalogue; DBIE carries them in the "Key Rates" indicators report
    (report id 531, "Indicators > Financial Sector Indicators > Key Rates"),
    which sits behind the BOE OpenDocument guest-token chain. Their config
    entries therefore ship with empty ``params`` and are skipped with a log
    line until that chain is wired — per SPEC, unsynced beats fabricated.
  * Live reachability of data.rbi.org.in could not be verified from the
    build environment (restricted egress); tests run on recorded fixtures.

Series codes, services and parameters live in db_config.json ->
sources.rbi (single source of truth — no series codes in this file).
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
from typing import Any

import requests
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential_jitter

from ..benchmarks import upsert_benchmark_observation
from ..db import load_config
from ..ingestion import ingestion_run
from ..logging_config import get_logger
from ..macro import upsert_observation
from ..providers.ratelimit import TokenBucket

logger = get_logger("sources.rbi")

DEFAULT_REQUESTS_PER_MINUTE = 30
REQUEST_TIMEOUT = 30  # seconds
JOB = "rbi_macro"

_HEADERS = {
    "User-Agent": ("BazzarTerminal/1.6 (+https://github.com/Tech-ka-14/bazzar; macro data sync)"),
    "Accept": "application/json",
    "content-type": "application/json",
    "datatype": "application/json",
}

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}

# Candidate keys for the observation date / value in a DBIE result row
# (SDMX core first, then the plain-JSON variants seen in gateway responses).
_DATE_KEYS = ("TIME_PERIOD", "time_period", "TimePeriod", "date", "Date", "period")
_VALUE_KEYS = ("OBS_VALUE", "obs_value", "obsValue", "value", "Value", "VALUE")


class SourceError(Exception):
    """Fatal error talking to a data source (after retries)."""


def rbi_config() -> dict[str, Any]:
    """The ``sources.rbi`` block of db_config.json."""
    return load_config()["sources"]["rbi"]


def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, (requests.RequestException, ConnectionError, TimeoutError))


def _extract_rows(payload: Any) -> list[dict[str, Any]]:
    """Find the list of row dicts inside a DBIE gateway payload.

    Tolerates the documented envelopes: the gateway wrapper
    ``{"body": {"result": [{"data": {"result": [...]}}]}}``, a plain
    ``{"data": [...]}`` / ``{"result": [...]}`` container, or a bare list.
    """
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if not isinstance(payload, dict):
        return []
    # Gateway envelope: body.result[0].data.result
    body = payload.get("body")
    if isinstance(body, dict):
        result = body.get("result")
        if isinstance(result, list):
            rows: list[dict[str, Any]] = []
            for item in result:
                if isinstance(item, dict):
                    data = item.get("data")
                    if isinstance(data, dict) and isinstance(data.get("result"), list):
                        rows.extend(r for r in data["result"] if isinstance(r, dict))
                    elif isinstance(item.get("rows"), list):
                        rows.extend(r for r in item["rows"] if isinstance(r, dict))
            if rows:
                return rows
    for key in ("data", "result", "rows", "observations"):
        value = payload.get(key)
        if isinstance(value, list):
            return [r for r in value if isinstance(r, dict)]
    return []


def _parse_obs_date(raw: Any) -> str | None:
    """Normalise a DBIE time period to an ISO date (YYYY-MM-DD), or None.

    Handles YYYY-MM-DD, DD-MM-YYYY / DD/MM/YYYY (RBI convention), YYYY-MM
    (monthly series -> first of month) and YYYY (annual -> 1 Jan).
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        return text
    m = re.fullmatch(r"(\d{2})[-/](\d{2})[-/](\d{4})", text)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return dt.date(year, month, day).isoformat()
        except ValueError:
            return None
    m = re.fullmatch(r"(\d{4})-(\d{2})", text)
    if m:
        return f"{text}-01"
    if re.fullmatch(r"\d{4}", text):
        return f"{text}-01-01"
    return None


def _as_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-", "NA", "N/A"):
            return None
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _matches_dimension(row: dict[str, Any], column: str, wanted: list[str]) -> bool:
    """True when the row's dimension cell matches one of ``wanted`` (code or
    label, case-insensitive; numeric values compare by value)."""
    cell = row.get(column)
    if cell is None:
        return False
    cell_s = str(cell).strip().casefold()
    for w in wanted:
        w_s = str(w).strip().casefold()
        if cell_s == w_s:
            return True
        try:  # "10" vs "10.0"
            if float(cell_s) == float(w_s):
                return True
        except ValueError:
            continue
    return False


def _row_to_observation(
    row: dict[str, Any],
) -> dict[str, Any] | None:
    """One raw DBIE row -> {"date": YYYY-MM-DD, "value": float} or None."""
    date_raw = next((row[k] for k in _DATE_KEYS if k in row), None)
    value_raw = next((row[k] for k in _VALUE_KEYS if k in row), None)
    date = _parse_obs_date(date_raw)
    value = _as_float(value_raw)
    if date is None or value is None:
        return None
    return {"date": date, "value": value}


def parse_dbie_series(
    payload: Any,
    *,
    dimension_column: str | None = None,
    dimension_values: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Pure parser: DBIE gateway payload -> [{"date", "value"}] observations.

    When ``dimension_column`` is given, only rows whose cell matches one of
    ``dimension_values`` (code or label) are kept — this is how a single DSD
    element (e.g. YIELD_GOV_SEC_RN) is sliced into 5Y / 10Y series. Rows with
    an unparseable date or a missing/blank value are dropped (never
    defaulted). Output is sorted by date, de-duplicated (last wins).
    """
    rows = _extract_rows(payload)
    out: dict[str, float] = {}
    for row in rows:
        if dimension_column and not _matches_dimension(
            row, dimension_column, dimension_values or []
        ):
            continue
        obs = _row_to_observation(row)
        if obs is not None:
            out[obs["date"]] = obs["value"]
    return [{"date": d, "value": out[d]} for d in sorted(out)]


class RbiSource:
    """HTTP client for the RBI DBIE gateway (injectable session for tests)."""

    name = "rbi_dbie"

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
        self.config = config or rbi_config()
        self._token: str | None = None

    # --- HTTP plumbing ------------------------------------------------------

    def _gateway_url(self, service: str) -> str:
        base = self.config["base_url"].rstrip("/")
        return f"{base}{self.config['gateway_path']}/{service}"

    def _post(self, service: str, body: dict[str, Any]) -> Any:
        """POST a gateway service with retry/backoff on 429/5xx and network
        errors; returns the raw response object."""

        def _do() -> Any:
            self._bucket.acquire()
            headers = dict(self.config.get("extra_headers") or {})
            if "channel_key" in self.config:
                headers.setdefault("channelkey", self.config["channel_key"])
            if self._token:
                headers["authorization"] = self._token
            resp = self._session.post(
                self._gateway_url(service),
                json={"body": body},
                headers=headers,
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
        """Gateway responses are HTML-entity-encoded JSON."""
        text = resp.text if hasattr(resp, "text") else resp.content.decode("utf-8")
        try:
            return json.loads(html.unescape(text))
        except json.JSONDecodeError as exc:
            raise SourceError(f"DBIE response is not JSON: {exc}") from exc

    def _ensure_token(self) -> None:
        """Guest session bearer via security_generateSessionToken."""
        if self._token is not None:
            return
        resp = self._post(self.config["token_service"], {})
        headers = getattr(resp, "headers", {}) or {}
        token = headers.get("authorization") or headers.get("Authorization")
        if not token:
            raise SourceError("DBIE session bootstrap returned no Authorization header")
        self._token = str(token)

    # --- data access ----------------------------------------------------------

    def series_entry(self, local_key: str) -> dict[str, Any] | None:
        """Config entry for a local series key (macro or benchmark map)."""
        for group in ("macro_series", "benchmark_series"):
            entry = self.config.get(group, {}).get(local_key)
            if entry is not None:
                return entry
        return None

    def fetch_series(self, local_key: str) -> list[dict[str, Any]]:
        """Fetch one configured series -> [{"date", "value"}] observations.

        Raises KeyError for an unconfigured key and SourceError when the
        config entry carries no fetch parameters (documented gap — the caller
        skips; nothing is fabricated).
        """
        entry = self.series_entry(local_key)
        if entry is None:
            raise KeyError(f"no sources.rbi config entry for series '{local_key}'")
        params = entry.get("params")
        if not params:
            raise SourceError(
                f"series '{local_key}' has no DBIE fetch parameters configured"
                " (see the note in db_config.json -> sources.rbi)"
            )
        self._ensure_token()
        service = entry.get("service") or self.config["data_service"]
        resp = self._post(service, dict(params))
        return parse_dbie_series(
            self._decode_payload(resp),
            dimension_column=entry.get("dimension_column"),
            dimension_values=entry.get("dimension_values"),
        )


def _sync_series(
    source: RbiSource, local_key: str, entry: dict[str, Any]
) -> tuple[list[dict[str, Any]], str | None]:
    """Fetch one series; returns (observations, error_message)."""
    try:
        return source.fetch_series(local_key), None
    except (SourceError, KeyError, requests.RequestException) as exc:
        logger.warning("rbi series fetch failed", series=local_key, error=str(exc))
        return [], f"{local_key}: {exc}"


def sync(con, source: RbiSource | None = None) -> dict[str, Any]:
    """Fetch all configured RBI series into macro/benchmark observations.

    Returns a summary dict {"macro": {key: n}, "benchmark": {key: n},
    "skipped": [keys]}. Per-series failures are logged, counted and recorded
    on the ingestion run (status=partial) — the remaining series still sync.
    """
    source = source or RbiSource()
    config = source.config
    summary: dict[str, Any] = {"macro": {}, "benchmark": {}, "skipped": []}
    errors: list[str] = []
    with ingestion_run(con, JOB) as run:
        for key, entry in config.get("macro_series", {}).items():
            obs, error = _sync_series(source, key, entry)
            if error:
                errors.append(error)
                summary["skipped"].append(key)
                continue
            scale = float(entry.get("value_scale", 1.0))
            for o in obs:
                # macro observations are period-keyed; period = YYYY-MM of the
                # observation date (SPEC: period labels like 2025-06).
                upsert_observation(con, key, o["date"][:7], o["value"] * scale)
                run.rows_written += 1
            summary["macro"][key] = len(obs)
        for key, entry in config.get("benchmark_series", {}).items():
            obs, error = _sync_series(source, key, entry)
            if error:
                errors.append(error)
                summary["skipped"].append(key)
                continue
            scale = float(entry.get("value_scale", 1.0))
            for o in obs:
                upsert_benchmark_observation(con, key, o["date"], o["value"] * scale)
                run.rows_written += 1
            summary["benchmark"][key] = len(obs)
        if errors:
            run.error = "; ".join(errors)[:1000]
    return summary
