"""Zerodha Kite Connect provider (P3 — primary market-data source).

Implements the ``MarketDataProvider`` protocol on the official ``kiteconnect``
SDK. Design rules (from BAZZAR_ROADMAP.md Phase 3):

  * daily timeframe only — ``interval="day"`` is hardcoded;
  * daily-candle history is capped at ~2000 days per API call → requests are
    chunked (a 10-year backfill is 2 chunks per symbol);
  * ~2.5 requests/second with jitter; exponential backoff on 429/5xx/network
    errors via tenacity;
  * ``TokenException``/``PermissionException`` → :class:`KiteAuthRequired`;
    callers must abort the run and ask the user to re-authenticate — Kite
    access tokens expire daily by design, retry-looping is pointless;
  * the historical API needs ``instrument_token``s, resolved from a
    ``{(symbol, exchange): token}`` map populated by
    ``backend.sync_instruments`` into the ``securities`` table.

The SDK client can be injected (``client=``) so tests run without network or
credentials.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from typing import Any

from kiteconnect import KiteConnect
from kiteconnect import exceptions as kite_exc
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential_jitter

from .base import (
    Bar,
    Instrument,
    ProviderAuthRequired,
    ProviderError,
    Quote,
)
from .ratelimit import TokenBucket

LOGIN_BASE_URL = "https://kite.trade/connect/login"
HISTORICAL_MAX_DAYS = 2000  # Kite caps daily-candle windows at ~2000 days
DEFAULT_REQUESTS_PER_MINUTE = 150  # ~2.5 req/s, under Kite's ~3 req/s history limit

TokenMap = dict[tuple[str, str], int]

_RETRYABLE = (
    kite_exc.NetworkException,  # includes HTTP 429 and 5xx
    kite_exc.GeneralException,
    ConnectionError,
    TimeoutError,
)
_AUTH_ERRORS = (kite_exc.TokenException, kite_exc.PermissionException)


class KiteAuthRequired(ProviderAuthRequired):
    """Kite session missing or expired — the user must re-authenticate."""


def login_url(api_key: str) -> str:
    """The Zerodha redirect-login URL for this app."""
    return f"{LOGIN_BASE_URL}?api_key={api_key}&v=3"


def day_chunks(start: dt.date, end: dt.date, max_days: int = HISTORICAL_MAX_DAYS):
    """Split [start, end] into inclusive windows of at most ``max_days`` days."""
    chunks: list[tuple[dt.date, dt.date]] = []
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + dt.timedelta(days=max_days - 1), end)
        chunks.append((cursor, chunk_end))
        cursor = chunk_end + dt.timedelta(days=1)
    return chunks


class KiteProvider:
    """``MarketDataProvider`` over Zerodha Kite Connect (daily only)."""

    name = "kite"

    def __init__(
        self,
        api_key: str,
        access_token: str,
        *,
        token_map: TokenMap | None = None,
        requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE,
        client: Any | None = None,
    ):
        if not api_key:
            raise ProviderError("KITE_API_KEY is not configured (set it in .env).")
        if not access_token:
            raise KiteAuthRequired(
                "No Kite access token in the OS keyring — connect via the "
                "'Connect Kite' button or GET /api/auth/kite/login-url."
            )
        self.api_key = api_key
        self._kite = (
            client
            if client is not None
            else KiteConnect(api_key=api_key, access_token=access_token)
        )
        self._tokens: TokenMap = token_map or {}
        self._bucket = TokenBucket(requests_per_minute, jitter_seconds=0.05)

    # --- internal helpers ---------------------------------------------------

    @staticmethod
    def _is_retryable(exc: BaseException) -> bool:
        return isinstance(exc, _RETRYABLE) and not isinstance(exc, _AUTH_ERRORS)

    def _call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Rate-limit + retry one SDK call; map auth errors, never retry them."""
        for attempt in Retrying(
            retry=retry_if_exception(self._is_retryable),
            stop=stop_after_attempt(5),
            wait=wait_exponential_jitter(initial=1, max=30),
            reraise=True,
        ):
            with attempt:
                self._bucket.acquire()
                try:
                    return fn(*args, **kwargs)
                except _AUTH_ERRORS as exc:
                    raise KiteAuthRequired(
                        f"Kite session rejected ({exc.__class__.__name__}) — re-authenticate."
                    ) from exc
        raise ProviderError("unreachable: retry loop exited without result")

    def _resolve_token(self, symbol: str, exchange: str) -> int:
        token = self._tokens.get((symbol, exchange))
        if token is None:
            raise ProviderError(
                f"no instrument_token for {exchange}:{symbol} — run "
                "`python -m backend.sync_instruments --provider kite` first."
            )
        return token

    # --- MarketDataProvider ---------------------------------------------------

    def history_daily(self, symbol: str, exchange: str, start: str, end: str) -> list[Bar]:
        token = self._resolve_token(symbol, exchange)
        start_d = dt.date.fromisoformat(start)
        end_d = dt.date.fromisoformat(end)
        by_date: dict[str, Bar] = {}
        for chunk_start, chunk_end in day_chunks(start_d, end_d):
            candles = self._call(
                self._kite.historical_data,
                token,
                chunk_start,
                chunk_end,
                interval="day",
                continuous=False,
                oi=False,
            )
            for candle in candles or []:
                bar = _normalize_candle(candle)
                if bar is not None:
                    by_date[bar["date"]] = bar
        return [by_date[d] for d in sorted(by_date)]

    def quotes(self, symbols: list[tuple[str, str]]) -> dict[str, Quote]:
        if not symbols:
            return {}
        keys = [f"{_kite_exchange(exchange)}:{symbol}" for symbol, exchange in symbols]
        payload = self._call(self._kite.quote, *keys)
        out: dict[str, Quote] = {}
        for (symbol, exchange), key in zip(symbols, keys, strict=True):
            data = (payload or {}).get(key) or {}
            last_price = data.get("last_price")
            out[symbol] = Quote(
                symbol=symbol,
                exchange=exchange,
                last_price=float(last_price) if last_price is not None else None,
                as_of=str(data["timestamp"]) if data.get("timestamp") else None,
            )
        return out

    def instruments(self, exchange: str | None = None) -> list[Instrument]:
        rows = (
            self._call(self._kite.instruments, exchange)
            if exchange
            else self._call(self._kite.instruments)
        )
        return [_to_instrument(r) for r in rows or []]


def _kite_exchange(exchange: str) -> str:
    """Bazzar exchange labels → Kite exchange labels (index instruments live
    on the base exchange in Kite's dumps)."""
    return exchange.removesuffix("_INDEX")


def _normalize_candle(candle: dict[str, Any]) -> Bar | None:
    raw_date = candle.get("date")
    if raw_date is None or candle.get("close") is None:
        return None
    if isinstance(raw_date, dt.datetime):
        day = raw_date.date().isoformat()
    else:
        day = str(raw_date)[:10]
    volume = candle.get("volume")
    return {
        "date": day,
        "open": _as_float(candle.get("open")),
        "high": _as_float(candle.get("high")),
        "low": _as_float(candle.get("low")),
        "close": float(candle["close"]),
        "volume": int(volume) if volume is not None else None,
    }


def _as_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _to_instrument(row: dict[str, Any]) -> Instrument:
    return Instrument(
        symbol=str(row.get("tradingsymbol") or ""),
        exchange=str(row.get("exchange") or ""),
        name=str(row.get("name") or ""),
        instrument_type=str(row.get("instrument_type") or ""),
        isin=row.get("isin"),
        instrument_token=_as_int(row.get("instrument_token")),
        lot_size=_as_int(row.get("lot_size")),
        tick_size=_as_float(row.get("tick_size")),
        segment=str(row.get("segment") or ""),
    )


def _as_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
