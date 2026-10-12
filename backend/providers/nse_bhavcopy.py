"""NSE bhavcopy fallback provider (P3, roadmap step 3.6).

Downloads the official daily equity bhavcopy from NSE's public archives
(``nsearchives.nseindia.com``) and normalises it into Bars. This is the EOD
fallback when Kite auth/quota fails, and doubles as a free reconciliation
source (roadmap 4.5).

Notes & limits:
  * NSE equity (cash segment) only, series ``EQ``; indices/BSE are out of
    scope for this provider (``ProviderCapabilityError``).
  * One HTTP request per trading day → ideal for top-ups (yesterday/today),
    too slow for multi-year backfills. Fetchers keep checkpoint discipline.
  * Polite client: explicit User-Agent/Referer, conservative rate limit.

The HTTP session is injectable for tests (no network in CI).
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import zipfile
from typing import Any

import requests
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential_jitter

from .base import Bar, Instrument, ProviderCapabilityError, ProviderError, Quote
from .ratelimit import TokenBucket

ARCHIVE_BASE = "https://nsearchives.nseindia.com/content/cm"
DEFAULT_REQUESTS_PER_MINUTE = 30
REQUEST_TIMEOUT = 30  # seconds
EQUITY_SERIES = "EQ"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/csv,application/zip,application/octet-stream,*/*",
    "Referer": "https://www.nseindia.com/all-reports",
}

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def bhavcopy_url(day: dt.date) -> str:
    """Archive URL of the unified NSE cash-market bhavcopy for ``day``."""
    return f"{ARCHIVE_BASE}/BhavCopy_NSE_CM_0_0_0_{day:%Y%m%d}_F_0000.CSV.zip"


def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, (requests.RequestException, ConnectionError, TimeoutError))


def parse_bhavcopy_csv(text: str, day: dt.date) -> list[dict[str, Any]]:
    """Parse the unified bhavcopy CSV into raw equity rows (dicts)."""
    rows: list[dict[str, Any]] = []
    reader = csv.DictReader(io.StringIO(text))
    for record in reader:
        if (record.get("SctySrs") or "").strip() != EQUITY_SERIES:
            continue
        rows.append(
            {
                "symbol": (record.get("TckrSymb") or "").strip(),
                "date": day.isoformat(),
                "open": _as_float(record.get("OpnPric")),
                "high": _as_float(record.get("HghPric")),
                "low": _as_float(record.get("LwPric")),
                "close": _as_float(record.get("ClsPric")),
                "volume": _as_int(record.get("TtlTradgVol")),
            }
        )
    return rows


def _as_float(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    try:
        return int(float(value)) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


class NseBhavcopyProvider:
    """``MarketDataProvider`` over NSE's official daily bhavcopy archives."""

    name = "nse_bhavcopy"

    def __init__(
        self,
        *,
        requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE,
        session: Any | None = None,
    ):
        self._session = session or requests.Session()
        self._session.headers.update(_HEADERS)
        self._bucket = TokenBucket(requests_per_minute, jitter_seconds=0.1)

    # --- internal -----------------------------------------------------------

    def _download(self, day: dt.date) -> bytes | None:
        """Raw bhavcopy bytes for ``day``; None when the archive has no file
        for the date (weekend/holiday). Retries 429/5xx with backoff."""

        def _get() -> bytes | None:
            self._bucket.acquire()
            resp = self._session.get(bhavcopy_url(day), timeout=REQUEST_TIMEOUT)
            if resp.status_code == 404:
                return None
            if resp.status_code in _RETRYABLE_STATUS:
                resp.raise_for_status()  # triggers tenacity retry
            resp.raise_for_status()
            return resp.content

        for attempt in Retrying(
            retry=retry_if_exception(_is_retryable),
            stop=stop_after_attempt(4),
            wait=wait_exponential_jitter(initial=1, max=20),
            reraise=True,
        ):
            with attempt:
                return _get()
        raise ProviderError("unreachable: retry loop exited without result")

    @staticmethod
    def _unzip(payload: bytes) -> str:
        if payload[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
                if not names:
                    raise ProviderError("bhavcopy archive contains no CSV file")
                return archive.read(names[0]).decode("utf-8-sig")
        return payload.decode("utf-8-sig")  # plain CSV fallback

    # --- bulk day access -----------------------------------------------------

    def fetch_day(self, day: dt.date) -> list[dict[str, Any]]:
        """All equity rows for one trading day (empty list on 404/holiday)."""
        payload = self._download(day)
        if payload is None:
            return []
        return parse_bhavcopy_csv(self._unzip(payload), day)

    # --- MarketDataProvider ---------------------------------------------------

    def history_daily(self, symbol: str, exchange: str, start: str, end: str) -> list[Bar]:
        if exchange != "NSE":
            raise ProviderCapabilityError(
                f"the bhavcopy provider covers NSE equity only, not {exchange!r}"
            )
        start_d = dt.date.fromisoformat(start)
        end_d = dt.date.fromisoformat(end)
        bars: list[Bar] = []
        day = start_d
        while day <= end_d:
            if day.weekday() < 5:  # cheap weekend skip; holidays 404 naturally
                for row in self.fetch_day(day):
                    if row["symbol"] == symbol and row["close"] is not None:
                        bars.append(
                            {
                                "date": row["date"],
                                "open": row["open"],
                                "high": row["high"],
                                "low": row["low"],
                                "close": row["close"],
                                "volume": row["volume"],
                            }
                        )
            day += dt.timedelta(days=1)
        bars.sort(key=lambda b: b["date"])
        return bars

    def quotes(self, symbols: list[tuple[str, str]]) -> dict[str, Quote]:
        raise ProviderCapabilityError("the bhavcopy provider is end-of-day only — no live quotes")

    def instruments(self, exchange: str | None = None) -> list[Instrument]:
        raise ProviderCapabilityError(
            "the bhavcopy provider has no security master — use Kite's "
            "instrument sync (python -m backend.sync_instruments --provider kite)"
        )
