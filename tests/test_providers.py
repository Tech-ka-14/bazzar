"""P3: provider-layer tests — Kite provider (mocked SDK), provider factory,
token bucket, and the NSE bhavcopy fallback. No network, no real credentials.
"""

from __future__ import annotations

import datetime as dt
import io
import time
import zipfile

import pytest
from kiteconnect import exceptions as kite_exc

from backend.db import get_connection, initialize_database
from backend.providers import PROVIDERS, load_token_map
from backend.providers.base import (
    Instrument,
    ProviderCapabilityError,
    ProviderError,
)
from backend.providers.kite import (
    HISTORICAL_MAX_DAYS,
    KiteAuthRequired,
    KiteProvider,
    day_chunks,
    login_url,
)
from backend.providers.nse_bhavcopy import (
    NseBhavcopyProvider,
    bhavcopy_url,
    parse_bhavcopy_csv,
)
from backend.providers.ratelimit import TokenBucket


class FakeKite:
    """Test double for kiteconnect.KiteConnect (no network)."""

    def __init__(self):
        self.candles: list[dict] = []
        self.quote_payload: dict = {}
        self.instrument_rows: list[dict] = []
        self.failures: list[Exception] = []
        self.history_calls: list[dict] = []

    def _maybe_fail(self):
        if self.failures:
            raise self.failures.pop(0)

    def historical_data(self, token, start, end, interval=None, continuous=None, oi=None):
        self.history_calls.append(
            {"token": token, "start": start, "end": end, "interval": interval}
        )
        self._maybe_fail()
        return list(self.candles)

    def quote(self, *keys):
        self._maybe_fail()
        return dict(self.quote_payload)

    def instruments(self, exchange=None):
        self._maybe_fail()
        return list(self.instrument_rows)


def _provider(fake: FakeKite, token_map=None) -> KiteProvider:
    return KiteProvider(
        "kite-key",
        "access-token",
        token_map=token_map if token_map is not None else {("INFY", "NSE"): 123},
        client=fake,
    )


# --- day chunking -------------------------------------------------------------


def test_day_chunks_split_at_max_days():
    chunks = day_chunks(dt.date(2016, 1, 1), dt.date(2026, 1, 1))
    assert len(chunks) == 2
    assert chunks[0] == (dt.date(2016, 1, 1), dt.date(2021, 6, 22))
    assert chunks[1] == (dt.date(2021, 6, 23), dt.date(2026, 1, 1))
    for start, end in chunks:
        assert (end - start).days < HISTORICAL_MAX_DAYS


def test_day_chunks_short_window_is_single_chunk():
    chunks = day_chunks(dt.date(2025, 1, 1), dt.date(2025, 12, 31))
    assert chunks == [(dt.date(2025, 1, 1), dt.date(2025, 12, 31))]


# --- history -------------------------------------------------------------------


def test_ten_year_backfill_is_chunked():
    fake = FakeKite()
    provider = _provider(fake)
    provider.history_daily("INFY", "NSE", "2016-01-01", "2026-01-01")
    assert len(fake.history_calls) == 2
    for call in fake.history_calls:
        assert call["token"] == 123
        assert call["interval"] == "day"
        assert (call["end"] - call["start"]).days < HISTORICAL_MAX_DAYS


def test_history_normalises_dedupes_and_sorts():
    fake = FakeKite()
    fake.candles = [
        {
            "date": dt.datetime(2025, 1, 7, 15, 30),
            "open": 10.0,
            "high": 11.0,
            "low": 9.5,
            "close": 10.5,
            "volume": 100,
        },
        {
            "date": dt.datetime(2025, 1, 6, 15, 30),
            "open": 9.0,
            "high": 10.0,
            "low": 8.5,
            "close": 9.5,
            "volume": 200,
        },
        {  # duplicate date wins-last, then sorted ascending
            "date": "2025-01-07",
            "open": 10.0,
            "high": 11.5,
            "low": 9.5,
            "close": 11.0,
            "volume": 300,
        },
    ]
    bars = _provider(fake).history_daily("INFY", "NSE", "2025-01-01", "2025-01-31")
    assert [b["date"] for b in bars] == ["2025-01-06", "2025-01-07"]
    assert bars[1]["close"] == 11.0
    assert bars[1]["volume"] == 300
    assert bars[0] == {
        "date": "2025-01-06",
        "open": 9.0,
        "high": 10.0,
        "low": 8.5,
        "close": 9.5,
        "volume": 200,
    }


def test_history_requires_instrument_token():
    fake = FakeKite()
    provider = _provider(fake, token_map={})
    with pytest.raises(ProviderError, match="sync_instruments"):
        provider.history_daily("INFY", "NSE", "2025-01-01", "2025-01-31")
    assert fake.history_calls == []


def test_auth_error_raises_immediately_without_retry():
    fake = FakeKite()
    fake.failures = [kite_exc.TokenException("token expired")]
    provider = _provider(fake)
    with pytest.raises(KiteAuthRequired):
        provider.history_daily("INFY", "NSE", "2025-01-01", "2025-01-31")
    assert len(fake.history_calls) == 1  # never retried


def test_network_errors_are_retried_then_succeed():
    fake = FakeKite()
    fake.failures = [
        kite_exc.NetworkException("boom"),
        kite_exc.NetworkException("boom again"),
    ]
    fake.candles = [
        {
            "date": dt.datetime(2025, 1, 6),
            "open": 1.0,
            "high": 2.0,
            "low": 0.5,
            "close": 1.5,
            "volume": 10,
        }
    ]
    bars = _provider(fake).history_daily("INFY", "NSE", "2025-01-06", "2025-01-06")
    assert len(fake.history_calls) == 3  # 2 failures + 1 success
    assert len(bars) == 1


def test_missing_access_token_means_auth_required():
    with pytest.raises(KiteAuthRequired):
        KiteProvider("kite-key", "", client=FakeKite())


def test_missing_api_key_is_config_error():
    with pytest.raises(ProviderError, match="KITE_API_KEY"):
        KiteProvider("", "access-token", client=FakeKite())


# --- quotes + instruments --------------------------------------------------------


def test_quotes_map_last_price_and_strip_index_suffix():
    fake = FakeKite()
    fake.quote_payload = {
        "NSE:INFY": {"last_price": 1500.25, "timestamp": "2025-01-06T15:30:00+05:30"},
        "NSE:NIFTY 50": {"last_price": 24000.0},
    }
    out = _provider(fake).quotes([("INFY", "NSE"), ("NIFTY 50", "NSE_INDEX")])
    assert out["INFY"].last_price == 1500.25
    assert out["INFY"].as_of == "2025-01-06T15:30:00+05:30"
    assert out["NIFTY 50"].last_price == 24000.0
    assert out["NIFTY 50"].as_of is None  # never fabricated


def test_instruments_mapping():
    fake = FakeKite()
    fake.instrument_rows = [
        {
            "tradingsymbol": "INFY",
            "exchange": "NSE",
            "name": "INFOSYS",
            "instrument_type": "EQ",
            "isin": "INE009A01021",
            "instrument_token": 408065,
            "lot_size": 1,
            "tick_size": 0.05,
            "segment": "NSE",
        }
    ]
    out = _provider(fake).instruments("NSE")
    assert out == [
        Instrument(
            symbol="INFY",
            exchange="NSE",
            name="INFOSYS",
            instrument_type="EQ",
            isin="INE009A01021",
            instrument_token=408065,
            lot_size=1,
            tick_size=0.05,
            segment="NSE",
        )
    ]


def test_login_url_shape():
    assert login_url("abc123") == "https://kite.trade/connect/login?api_key=abc123&v=3"


# --- factory + token map ----------------------------------------------------------


def test_factory_rejects_unknown_provider():
    from backend.providers import get_provider

    with pytest.raises(ProviderError, match="unknown market-data provider"):
        get_provider("not-a-provider")


def test_factory_builds_openalgo(monkeypatch):
    from backend.providers import get_provider
    from backend.providers.openalgo import OpenAlgoProvider

    monkeypatch.setenv("OPENALGO_API_KEY", "test-key")
    provider = get_provider("openalgo")
    assert isinstance(provider, OpenAlgoProvider)
    assert provider.name == "openalgo"


def test_factory_builds_kite_from_settings_and_keyring(monkeypatch):
    import backend.kite_auth as kite_auth
    from backend.providers import get_provider
    from backend.providers.kite import KiteProvider
    from backend.settings import get_settings

    monkeypatch.setenv("KITE_API_KEY", "kite-key")
    monkeypatch.setattr(kite_auth, "get_access_token", lambda: "access-token")
    get_settings.cache_clear()
    try:
        provider = get_provider("kite")
    finally:
        get_settings.cache_clear()
    assert isinstance(provider, KiteProvider)
    assert provider.name == "kite"


def test_load_token_map(tmp_path, monkeypatch):
    monkeypatch.setenv("BAZZAR_DATA_DIR", str(tmp_path))
    initialize_database()
    con = get_connection()
    try:
        con.execute(
            "INSERT INTO securities (symbol, name, exchange, instrument_type, isin, active,"
            " instrument_token) VALUES ('INFY', 'Infosys', 'NSE', 'EQ', NULL, TRUE, 408065)"
        )
        con.execute(
            "INSERT INTO securities (symbol, name, exchange, instrument_type, isin, active)"
            " VALUES ('NOTOKEN', 'No Token Ltd', 'NSE', 'EQ', NULL, TRUE)"
        )
        assert load_token_map(con) == {("INFY", "NSE"): 408065}
    finally:
        con.close()


# --- rate limiter -----------------------------------------------------------------


def test_token_bucket_throttles():
    bucket = TokenBucket(requests_per_minute=600)  # 10/s
    start = time.monotonic()
    for _ in range(12):  # 10 free + 2 throttled (~0.2s)
        bucket.acquire()
    assert time.monotonic() - start < 2.0  # generous bound, CI-safe
    assert bucket.tokens <= bucket.capacity


# --- NSE bhavcopy fallback ---------------------------------------------------------


CSV_HEADER = "TradDt,SctySrs,TckrSymb,OpnPric,HghPric,LwPric,ClsPric,TtlTradgVol\n"


def _zip_bytes(csv_text: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        archive.writestr("bhavcopy.csv", csv_text)
    return buf.getvalue()


class FakeResponse:
    def __init__(self, status_code: int, content: bytes = b""):
        self.status_code = status_code
        self.content = content

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses: list[FakeResponse]):
        self.headers: dict = {}
        self.responses = list(responses)
        self.calls: list[str] = []

    def get(self, url, timeout=None):
        self.calls.append(url)
        return self.responses.pop(0)


def test_bhavcopy_url_format():
    assert bhavcopy_url(dt.date(2025, 1, 6)) == (
        "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20250106_F_0000.CSV.zip"
    )


def test_parse_bhavcopy_csv_filters_equity_series():
    text = CSV_HEADER + (
        "2025-01-06,EQ,INFY,1500,1520,1490,1510,123456\n"
        "2025-01-06,BE,ODDLOT,10,11,9,10,5\n"
        "2025-01-06,EQ,TCS,4000,4050,3990,4040,999\n"
    )
    rows = parse_bhavcopy_csv(text, dt.date(2025, 1, 6))
    assert [r["symbol"] for r in rows] == ["INFY", "TCS"]  # BE series filtered out
    assert rows[0] == {
        "symbol": "INFY",
        "date": "2025-01-06",
        "open": 1500.0,
        "high": 1520.0,
        "low": 1490.0,
        "close": 1510.0,
        "volume": 123456,
    }


def test_bhavcopy_history_skips_holidays_and_filters_symbol():
    csv_text = CSV_HEADER + (
        "2025-01-06,EQ,INFY,1500,1520,1490,1510,123456\n2025-01-06,EQ,TCS,4000,4050,3990,4040,999\n"
    )
    session = FakeSession(
        [
            FakeResponse(200, _zip_bytes(csv_text)),  # Mon 2025-01-06
            FakeResponse(404),  # Tue 2025-01-07 — holiday: no archive
        ]
    )
    provider = NseBhavcopyProvider(session=session)
    bars = provider.history_daily("INFY", "NSE", "2025-01-06", "2025-01-07")
    assert len(bars) == 1
    assert bars[0]["date"] == "2025-01-06"
    assert bars[0]["close"] == 1510.0
    assert len(session.calls) == 2  # one request per weekday


def test_bhavcopy_nse_only():
    provider = NseBhavcopyProvider(session=FakeSession([]))
    with pytest.raises(ProviderCapabilityError):
        provider.history_daily("INFY", "BSE", "2025-01-06", "2025-01-07")


def test_bhavcopy_has_no_quotes_or_instruments():
    provider = NseBhavcopyProvider(session=FakeSession([]))
    with pytest.raises(ProviderCapabilityError):
        provider.quotes([("INFY", "NSE")])
    with pytest.raises(ProviderCapabilityError):
        provider.instruments("NSE")


def test_provider_registry():
    assert PROVIDERS == ("kite", "openalgo", "nse_bhavcopy")
