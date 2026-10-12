"""Provider registry + factory (P3).

Fetchers resolve their provider through :func:`get_provider` — the provider
name comes from ``--provider`` on the CLI or ``MARKET_DATA_PROVIDER`` in
settings (default ``openalgo`` until you switch to Kite).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import (
    Bar,
    Instrument,
    MarketDataProvider,
    ProviderAuthRequired,
    ProviderCapabilityError,
    ProviderError,
    Quote,
)

if TYPE_CHECKING:
    import duckdb

PROVIDERS = ("kite", "openalgo", "nse_bhavcopy")
DEFAULT_PROVIDER = "openalgo"

__all__ = [
    "Bar",
    "Instrument",
    "MarketDataProvider",
    "ProviderAuthRequired",
    "ProviderCapabilityError",
    "ProviderError",
    "Quote",
    "PROVIDERS",
    "DEFAULT_PROVIDER",
    "get_provider",
    "load_token_map",
]


def load_token_map(con: duckdb.DuckDBPyConnection) -> dict[tuple[str, str], int]:
    """{(symbol, exchange): instrument_token} from the securities master."""
    rows = con.execute(
        "SELECT symbol, exchange, instrument_token FROM securities"
        " WHERE instrument_token IS NOT NULL"
    ).fetchall()
    return {(str(s), str(e)): int(t) for s, e, t in rows}


def get_provider(
    name: str | None = None,
    *,
    con: duckdb.DuckDBPyConnection | None = None,
) -> MarketDataProvider:
    """Build the configured provider. Kite reads its session from the OS
    keyring and its instrument-token map from the DB (run sync_instruments
    first); auth problems raise ``ProviderAuthRequired`` — do not retry-loop."""
    from ..settings import get_settings

    settings = get_settings()
    chosen = (name or settings.market_data_provider or DEFAULT_PROVIDER).strip().lower()

    if chosen == "openalgo":
        from .openalgo import OpenAlgoProvider

        return OpenAlgoProvider()

    if chosen == "kite":
        from ..kite_auth import get_access_token
        from .kite import KiteProvider

        token_map = load_token_map(con) if con is not None else {}
        return KiteProvider(
            settings.kite_api_key,
            get_access_token() or "",
            token_map=token_map,
        )

    if chosen == "nse_bhavcopy":
        from .nse_bhavcopy import NseBhavcopyProvider

        return NseBhavcopyProvider()

    raise ProviderError(
        f"unknown market-data provider {chosen!r} — expected one of {', '.join(PROVIDERS)}"
    )
