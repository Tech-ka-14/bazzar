"""NSE public open-data source (P4-B, roadmap 4.3).

Fetches from the exchange's public (undocumented but stable) JSON APIs:

  * Market holidays:
        GET https://www.nseindia.com/api/holiday-master?type=trading
    -> upserted into ``trading_calendar`` (Capital Market segment, "CM").
    Special sessions that ARE trading days (Muhurat trading — official
    daily bars exist for them, see backend/data/nse_calendar.csv) are NOT
    marked as holidays: entries whose description flags a trading session
    are parsed as ``is_trading=True`` so is_trading_day() keeps returning
    True for those dates.
  * FII/DII daily cash-market flows:
        GET https://www.nseindia.com/api/fiidiiTradeReact
    -> date-keyed rows in ``benchmark_observations`` (series ``fii_net`` /
    ``dii_net``, ₹ crore, from the ``fii_dii`` benchmark group).
  * Index constituents (e.g. NIFTY 50):
        GET https://www.nseindia.com/api/equity-stockIndices?index=...
    -> cached as JSON under BAZZAR_DATA_DIR/cache/nse/ (reused when fresh);
    a data-access helper for future UI use — no DB table, and [] with a
    warning on failure (never fabricated).

NSE's site sits behind a cookie wall: a plain GET to https://www.nseindia.com
first bootstraps the session cookies (``_bootstrap_cookies``); 401/403
responses trigger one re-bootstrap + retry. Polite headers throughout
(User-Agent/Referer), TokenBucket rate limit, tenacity backoff on 429/5xx.

Endpoint paths live in db_config.json -> sources.nse_open (single source of
truth). Live reachability of www.nseindia.com could not be verified from the
build environment (restricted egress); tests run on recorded fixtures.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

import requests
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential_jitter

from ..benchmarks import upsert_benchmark_observation
from ..calendar import DEFAULT_EXCHANGE, upsert_trading_days
from ..db import get_data_dir, load_config
from ..ingestion import ingestion_run
from ..logging_config import get_logger
from ..providers.ratelimit import TokenBucket

logger = get_logger("sources.nse_open")

DEFAULT_REQUESTS_PER_MINUTE = 20
REQUEST_TIMEOUT = 30  # seconds
JOB = "nse_open"
CONSTITUENT_CACHE_HOURS = 6

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_REAUTH_STATUS = {401, 403}

# Descriptions like "Muhurat Trading" / "Diwali Muhurat session" are exchange
# holidays on paper but ARE trading sessions (official bars exist — see the
# seeded calendar); they must not flip is_trading_day to False.
_SPECIAL_TRADING_RE = re.compile(r"muhurat", re.IGNORECASE)


class SourceError(Exception):
    """Fatal error talking to a data source (after retries)."""


def nse_open_config() -> dict[str, Any]:
    """The ``sources.nse_open`` block of db_config.json."""
    return load_config()["sources"]["nse_open"]


def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, (requests.RequestException, ConnectionError, TimeoutError))


def _parse_nse_date(raw: Any) -> str | None:
    """Normalise an NSE date label to YYYY-MM-DD, or None.

    Handles "01-Jan-2026" / "26-January-2026" (NSE convention), YYYY-MM-DD
    and DD/MM/YYYY.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        return text
    for fmt in ("%d-%b-%Y", "%d-%B-%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return dt.datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _as_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-", "NA", "N/A"):
            return None
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def parse_holiday_master(
    payload: Any, segments: tuple[str, ...] = ("CM",)
) -> list[tuple[str, bool, str | None]]:
    """Pure parser: holiday-master payload -> [(date, is_trading, name)].

    The payload is keyed by market segment ("CM" = capital market, "FO",
    "CD", ...); only ``segments`` are read (default: CM). Dates are
    de-duplicated (last wins). Rows with an unparseable date are dropped.
    """
    out: dict[str, tuple[bool, str | None]] = {}
    if not isinstance(payload, dict):
        return []
    for segment in segments:
        rows = payload.get(segment)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            date = _parse_nse_date(
                row.get("tradingDate") or row.get("holidayDate") or row.get("date")
            )
            if date is None:
                continue
            name = (row.get("description") or row.get("holiday") or "").strip() or None
            is_trading = bool(name and _SPECIAL_TRADING_RE.search(name))
            out[date] = (is_trading, name)
    return [(d, out[d][0], out[d][1]) for d in sorted(out)]


def parse_fii_dii_flows(payload: Any) -> list[dict[str, Any]]:
    """Pure parser: fiidiiTradeReact payload -> one dict per date.

    The endpoint returns a flat list with separate FII ("FII/FPI *") and DII
    ("DII *") entries per day (values in ₹ crore). Output rows:
    {"date": YYYY-MM-DD, "fii_net": float|None, "dii_net": float|None},
    sorted by date. Entries with an unparseable date are dropped; a missing
    net value stays None (never defaulted).
    """
    rows = payload if isinstance(payload, list) else []
    by_date: dict[str, dict[str, Any]] = {}
    for item in rows:
        if not isinstance(item, dict):
            continue
        date = _parse_nse_date(item.get("date"))
        if date is None:
            continue
        category = str(item.get("category") or "").upper()
        net = _as_float(item.get("netValue"))
        entry = by_date.setdefault(date, {"date": date, "fii_net": None, "dii_net": None})
        if "FII" in category or "FPI" in category:
            entry["fii_net"] = net
        elif "DII" in category:
            entry["dii_net"] = net
    return [by_date[d] for d in sorted(by_date)]


def parse_index_constituents(payload: Any) -> list[dict[str, Any]]:
    """Pure parser: equity-stockIndices payload -> constituent rows.

    Keeps the ``data`` rows that carry a ``symbol``; the index's own summary
    row (``priority: 1``, symbol == index name) is dropped. Each kept row is
    reduced to {symbol, name, weight?} — weight is included only when the
    payload carries one (never fabricated).
    """
    if not isinstance(payload, dict):
        return []
    rows = payload.get("data")
    if not isinstance(rows, list):
        return []
    index_names = {str(payload.get("name") or "").strip()}
    meta = payload.get("metadata")
    if isinstance(meta, dict):
        index_names.add(str(meta.get("indexName") or "").strip())
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = (row.get("symbol") or "").strip()
        if not symbol or row.get("priority") == 1 or symbol in index_names:
            continue  # the index's own summary row, not a constituent
        meta = row.get("meta")
        name = ""
        if isinstance(meta, dict):
            name = str(meta.get("companyName") or "").strip()
        if not name:
            name = str(row.get("companyName") or "").strip()
        entry: dict[str, Any] = {"symbol": symbol, "name": name}
        weight = _as_float(row.get("ffmc") or row.get("weight") or row.get("weightage"))
        if weight is not None:
            entry["weight"] = weight
        out.append(entry)
    return out


class NseOpenSource:
    """HTTP client for NSE's public JSON APIs (injectable session for tests)."""

    name = "nse_open"

    def __init__(
        self,
        session: Any | None = None,
        *,
        requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE,
        config: dict[str, Any] | None = None,
        cache_dir: str | Path | None = None,
    ):
        self._session = session or requests.Session()
        self._session.headers.update(_HEADERS)
        self._bucket = TokenBucket(requests_per_minute, jitter_seconds=0.1)
        self.config = config or nse_open_config()
        self.cache_dir = Path(cache_dir) if cache_dir else get_data_dir() / "cache" / "nse"
        self._cookies_ready = False

    # --- HTTP plumbing ------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self.config['base_url'].rstrip('/')}{path}"

    def _bootstrap_cookies(self) -> None:
        """Prime the session cookies with a plain GET to the site root."""
        self._bucket.acquire()
        resp = self._session.get(self.config["base_url"], timeout=REQUEST_TIMEOUT)
        if resp.status_code in _RETRYABLE_STATUS:
            resp.raise_for_status()
        resp.raise_for_status()
        self._cookies_ready = True

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET an NSE API path with cookie bootstrap, one re-auth retry on
        401/403, and tenacity backoff on 429/5xx/network errors."""

        def _do() -> Any:
            if not self._cookies_ready:
                self._bootstrap_cookies()
            self._bucket.acquire()
            resp = self._session.get(self._url(path), params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code in _REAUTH_STATUS:
                self._cookies_ready = False
                self._bootstrap_cookies()
                self._bucket.acquire()
                resp = self._session.get(self._url(path), params=params, timeout=REQUEST_TIMEOUT)
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
            raise SourceError(f"NSE response is not JSON: {exc}") from exc

    # --- data access ----------------------------------------------------------

    def fetch_holidays(self) -> list[tuple[str, bool, str | None]]:
        """Trading-segment holidays -> [(date, is_trading, description)]."""
        resp = self._get(self.config["holidays_path"])
        segments = tuple(self.config.get("holiday_segments") or ("CM",))
        return parse_holiday_master(self._decode_payload(resp), segments)

    def fetch_fii_dii(self) -> list[dict[str, Any]]:
        """FII/DII daily flows -> [{"date", "fii_net", "dii_net"}]."""
        resp = self._get(self.config["fii_dii_path"])
        return parse_fii_dii_flows(self._decode_payload(resp))

    def index_constituents(self, index_name: str) -> list[dict[str, Any]]:
        """Constituents of an NSE index (cached aggressively).

        The raw response is cached under BAZZAR_DATA_DIR/cache/nse/ with a
        timestamp and reused while younger than ``constituent_cache_hours``.
        On fetch failure a stale cache is used if present; otherwise []
        is returned with a warning — nothing is fabricated.
        """
        slug = re.sub(r"[^A-Za-z0-9]+", "_", index_name).strip("_").lower()
        cache_path = self.cache_dir / f"index_constituents_{slug}.json"
        cache_hours = float(self.config.get("constituent_cache_hours", CONSTITUENT_CACHE_HOURS))
        cached = self._read_cache(cache_path)
        if cached is not None and cached["age_hours"] < cache_hours:
            logger.info(
                "nse constituents served from cache",
                index=index_name,
                age_hours=round(cached["age_hours"], 2),
            )
            return cached["rows"]
        try:
            resp = self._get(self.config["constituents_path"], params={"index": index_name})
            rows = parse_index_constituents(self._decode_payload(resp))
        except (SourceError, requests.RequestException) as exc:
            if cached is not None:
                logger.warning(
                    "nse constituents fetch failed — using stale cache",
                    index=index_name,
                    error=str(exc),
                )
                return cached["rows"]
            logger.warning(
                "nse constituents fetch failed — returning [] (never fabricate)",
                index=index_name,
                error=str(exc),
            )
            return []
        if not rows:
            logger.warning("nse constituents response carried no rows", index=index_name)
            return cached["rows"] if cached is not None else []
        self._write_cache(cache_path, rows)
        return rows

    # --- cache helpers --------------------------------------------------------

    @staticmethod
    def _read_cache(path: Path) -> dict[str, Any] | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            fetched_at = dt.datetime.fromisoformat(payload["fetched_at"])
            rows = payload["rows"]
            age = dt.datetime.now(dt.UTC).replace(tzinfo=None) - fetched_at
            return {"age_hours": age.total_seconds() / 3600, "rows": rows}
        except (OSError, ValueError, KeyError, TypeError):
            return None

    @staticmethod
    def _write_cache(path: Path, rows: list[dict[str, Any]]) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "fetched_at": dt.datetime.now(dt.UTC).replace(tzinfo=None).isoformat(),
                "rows": rows,
            }
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError as exc:
            logger.warning("nse constituents cache write failed", error=str(exc))


def sync(con, source: NseOpenSource | None = None) -> dict[str, Any]:
    """Fetch NSE holidays + FII/DII flows into the database.

    Returns {"holidays": n, "fii_dii": n, "skipped": [...]}. Per-dataset
    failures are logged, counted and recorded on the ingestion run
    (status=partial) — the remaining datasets still sync.
    """
    source = source or NseOpenSource()
    summary: dict[str, Any] = {"holidays": 0, "fii_dii": 0, "skipped": []}
    errors: list[str] = []
    with ingestion_run(con, JOB) as run:
        try:
            holidays = source.fetch_holidays()
            upsert_trading_days(
                con,
                [
                    (date, DEFAULT_EXCHANGE, is_trading, description)
                    for date, is_trading, description in holidays
                ],
            )
            run.rows_written += len(holidays)
            summary["holidays"] = len(holidays)
        except (SourceError, KeyError, requests.RequestException) as exc:
            logger.warning("nse holiday sync failed", error=str(exc))
            errors.append(f"holidays: {exc}")
            summary["skipped"].append("holidays")

        try:
            flows = source.fetch_fii_dii()
            written = 0
            for flow in flows:
                for series_key, value in (
                    ("fii_net", flow["fii_net"]),
                    ("dii_net", flow["dii_net"]),
                ):
                    if value is None:
                        continue
                    upsert_benchmark_observation(con, series_key, flow["date"], value)
                    written += 1
            run.rows_written += written
            summary["fii_dii"] = len(flows)
        except (SourceError, KeyError, requests.RequestException) as exc:
            logger.warning("nse fii/dii sync failed", error=str(exc))
            errors.append(f"fii_dii: {exc}")
            summary["skipped"].append("fii_dii")

        if errors:
            run.error = "; ".join(errors)[:1000]
    return summary
