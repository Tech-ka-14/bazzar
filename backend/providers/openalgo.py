"""OpenAlgo REST provider (Motilal Oswal broker) for the Bazzar data layer.

Moved from ``backend/openalgo_client.py`` in P3; the old module path remains
as a thin re-export shim. Implements the ``MarketDataProvider`` protocol via
``OpenAlgoProvider`` — kept as the optional fallback provider.

Credentials come from the environment or a repo-root `.env` file (parsed with
a tiny built-in parser — no external dependency):

    OPENALGO_BASE_URL   default http://127.0.0.1:5000
    OPENALGO_API_KEY    OpenAlgo host API key (required)
    BROKER_API_KEY      Motilal Oswal client code
    BROKER_API_SECRET   Motilal Oswal generated API key

Rate-limit policy: daily timeframe (`interval: "D"`) only — no smaller
timeframe is ever requested — and requests are throttled to
`fetch_policy.requests_per_minute` from db_config.json.
"""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
from typing import Any

import requests

from ..db import REPO_ROOT, load_config
from .base import Bar, Instrument, ProviderCapabilityError, Quote
from .ratelimit import TokenBucket

DEFAULT_BASE_URL = "http://127.0.0.1:5000"
REQUEST_TIMEOUT = 30  # seconds
INTERVAL = "D"  # daily only — hardcoded per fetch policy


class CredentialsNotConfigured(RuntimeError):
    """Raised when the OpenAlgo API key is missing from env/.env."""


def load_dotenv(path: str | None = None) -> dict[str, str]:
    """Minimal .env parser: KEY=VALUE lines, '#' comments, optional quotes.

    Does not override variables already present in os.environ. Returns the
    parsed key/value mapping.
    """
    env_path = Path(path) if path else REPO_ROOT / ".env"
    parsed: dict[str, str] = {}
    if not env_path.exists():
        return parsed
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        parsed[key] = value
        os.environ.setdefault(key, value)
    return parsed


class OpenAlgoClient:
    """Thin OpenAlgo REST client. Interval is hardcoded to daily ("D")."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        env_path: str | None = None,
        requests_per_minute: int | None = None,
    ):
        load_dotenv(env_path)
        self.base_url = (
            base_url or os.environ.get("OPENALGO_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("OPENALGO_API_KEY")
        self.broker_api_key = os.environ.get("BROKER_API_KEY")
        self.broker_api_secret = os.environ.get("BROKER_API_SECRET")
        if not self.api_key:
            raise CredentialsNotConfigured(
                "OPENALGO_API_KEY is not configured. Copy .env.example to .env "
                "and fill in your OpenAlgo/Motilal Oswal credentials."
            )
        rpm = requests_per_minute
        if rpm is None:
            rpm = load_config().get("fetch_policy", {}).get("requests_per_minute", 60)
        self._bucket = TokenBucket(rpm)
        self._session = requests.Session()

    def _post(self, endpoint: str, payload: dict[str, Any]) -> Any:
        self._bucket.acquire()
        url = f"{self.base_url}{endpoint}"
        body = {"apikey": self.api_key, **payload}
        resp = self._session.post(url, json=body, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def history(self, symbol: str, exchange: str, start_date: str, end_date: str) -> Any:
        """Daily OHLCV history. `interval` is always "D" (daily only)."""
        return self._post(
            "/api/v1/history",
            {
                "symbol": symbol,
                "exchange": exchange,
                "interval": INTERVAL,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

    def quotes(self, symbol: str, exchange: str) -> Any:
        return self._post("/api/v1/quotes", {"symbol": symbol, "exchange": exchange})

    def search(self, query: str) -> Any:
        return self._post("/api/v1/search", {"query": query})


_TIME_KEYS = ("timestamp", "datetime", "date", "time")


def _to_date_str(value: Any) -> str:
    """Normalise an epoch (s/ms) or ISO-ish timestamp to YYYY-MM-DD."""
    if isinstance(value, (int, float)):
        secs = value / 1000.0 if value > 1e12 else float(value)
        return dt.datetime.fromtimestamp(secs, tz=dt.UTC).date().isoformat()
    text = str(value).strip()
    return text[:10]


def normalize_history(payload: Any) -> list[Bar]:
    """Normalise an OpenAlgo /history response to a list of daily bars:
    [{date, open, high, low, close, volume}, ...] sorted by date ascending.

    Handles the response shapes OpenAlgo/brokers return: list-of-dicts,
    columnar dict-of-lists, and pandas split format ({columns, data}).
    Empty/errored responses yield an empty list (weekends/holidays are
    skipped naturally because the API simply returns no rows).
    """
    if not isinstance(payload, dict):
        return []
    if str(payload.get("status", "success")).lower() not in ("success", "ok"):
        return []
    data = payload.get("data", payload)
    rows: list[list[Any]] = []
    keys: list[str] = []
    if isinstance(data, dict) and "columns" in data and "data" in data:
        keys = [str(c).lower() for c in data["columns"]]
        rows = [list(r) for r in data["data"]]
    elif isinstance(data, dict):  # columnar dict of lists
        keys = [str(k).lower() for k in data.keys()]
        values = [list(v) for v in data.values()]
        rows = [list(r) for r in zip(*values, strict=False)] if values else []
    elif isinstance(data, list):
        if data and isinstance(data[0], dict):
            keys = [str(k).lower() for k in data[0].keys()]
            rows = [[item.get(k) for k in data[0].keys()] for item in data]
        else:
            return []
    else:
        return []

    def idx(*names: str) -> int | None:
        for n in names:
            if n in keys:
                return keys.index(n)
        return None

    i_time = idx(*_TIME_KEYS)
    i_open, i_high = idx("open"), idx("high")
    i_low, i_close = idx("low"), idx("close")
    i_vol = idx("volume")
    if i_time is None or i_close is None:
        return []

    bars = []
    for r in rows:
        try:
            bars.append(
                {
                    "date": _to_date_str(r[i_time]),
                    "open": float(r[i_open]) if i_open is not None else None,
                    "high": float(r[i_high]) if i_high is not None else None,
                    "low": float(r[i_low]) if i_low is not None else None,
                    "close": float(r[i_close]),
                    "volume": int(r[i_vol]) if i_vol is not None and r[i_vol] is not None else None,
                }
            )
        except (TypeError, ValueError):
            continue
    bars.sort(key=lambda b: str(b["date"]))
    return bars


class OpenAlgoProvider:
    """``MarketDataProvider`` adapter over :class:`OpenAlgoClient`."""

    name = "openalgo"

    def __init__(self, client: OpenAlgoClient | None = None, **client_kwargs: Any):
        self._client = client or OpenAlgoClient(**client_kwargs)

    def history_daily(self, symbol: str, exchange: str, start: str, end: str) -> list[Bar]:
        return normalize_history(self._client.history(symbol, exchange, start, end))

    def quotes(self, symbols: list[tuple[str, str]]) -> dict[str, Quote]:
        out: dict[str, Quote] = {}
        for symbol, exchange in symbols:
            payload = self._client.quotes(symbol, exchange)
            data = payload.get("data", payload) if isinstance(payload, dict) else {}
            last = None
            if isinstance(data, dict):
                for key in ("ltp", "last_price", "close"):
                    if data.get(key) is not None:
                        try:
                            last = float(data[key])
                        except (TypeError, ValueError):
                            last = None
                        break
            out[symbol] = Quote(symbol=symbol, exchange=exchange, last_price=last)
        return out

    def instruments(self, exchange: str | None = None) -> list[Instrument]:
        raise ProviderCapabilityError(
            "OpenAlgo has no security-master dump; use the Kite provider's "
            "instrument sync (python -m backend.sync_instruments --provider kite)."
        )
