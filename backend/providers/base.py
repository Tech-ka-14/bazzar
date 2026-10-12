"""Provider contracts for market-data sources (P3).

Every data source (OpenAlgo, Kite Connect, NSE bhavcopy, …) implements the
``MarketDataProvider`` protocol so fetchers stay provider-agnostic and tests
can inject fakes. Bars are plain dicts — the same shape
``backend.validation.validate_bars`` consumes:

    {"date": "YYYY-MM-DD", "open": float, "high": float, "low": float,
     "close": float, "volume": int | None}

Hard rules honoured here:
  * daily timeframe only — the protocol exposes no intraday method;
  * auth failures raise ``ProviderAuthRequired`` and callers must NOT
    retry-loop them (re-authentication is a user action);
  * unsupported capabilities raise ``ProviderCapabilityError`` — never a
    fabricated/empty stand-in that looks like real data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

# A normalised daily bar — see module docstring for the exact keys.
Bar = dict[str, Any]


@dataclass(frozen=True, slots=True)
class Instrument:
    """One row of a provider's security master."""

    symbol: str
    exchange: str
    name: str = ""
    instrument_type: str = ""
    isin: str | None = None
    instrument_token: int | None = None
    lot_size: int | None = None
    tick_size: float | None = None
    segment: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Quote:
    """A latest-price snapshot. ``as_of`` is None when the provider does not
    supply a timestamp — never a guessed value."""

    symbol: str
    exchange: str
    last_price: float | None
    as_of: str | None = None


class ProviderError(RuntimeError):
    """Base class for provider failures."""


class ProviderAuthRequired(ProviderError):
    """Authentication missing/expired — surface 're-authenticate' to the user.

    Fetchers must abort the run (checkpoint stays where it is) instead of
    retry-looping; Kite access tokens expire daily by design.
    """


class ProviderCapabilityError(ProviderError):
    """The provider does not support this operation (e.g. bhavcopy quotes)."""


@runtime_checkable
class MarketDataProvider(Protocol):
    """The contract every market-data source implements."""

    name: str

    def history_daily(self, symbol: str, exchange: str, start: str, end: str) -> list[Bar]:
        """Daily OHLCV bars for [start, end] (YYYY-MM-DD), sorted ascending."""
        ...

    def quotes(self, symbols: list[tuple[str, str]]) -> dict[str, Quote]:
        """Latest quotes for (symbol, exchange) pairs, keyed by symbol."""
        ...

    def instruments(self, exchange: str | None = None) -> list[Instrument]:
        """The provider's security master (one exchange or all)."""
        ...
