"""Pydantic response models for the Bazzar Terminal HTTP API (P5, roadmap 5.3).

Every ``response_model`` here is the *contract* the renderer relies on
(documented in SPEC.md "Local HTTP API contract"). FastAPI validates each
response against these models, so a shape regression fails loudly instead of
silently drifting the renderer contract.

Hard rule (SPEC): fields are nullable — never fabricated. When nothing has
been synced yet, numeric/date fields are ``None`` and lists are empty.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class Quote(BaseModel):
    """Latest close + pointwise/percent change; all None when unsynced."""

    value: float | None = None
    change: float | None = None
    changePct: float | None = None
    asOf: str | None = None


class HomeIndex(BaseModel):
    name: str
    symbol: str
    value: float | None = None
    change: float | None = None
    changePct: float | None = None
    asOf: str | None = None


class IndexRow(BaseModel):
    symbol: str
    name: str
    exchange: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    yearHigh: float | None = None
    yearLow: float | None = None
    asOf: str | None = None


class SearchResult(BaseModel):
    symbol: str
    name: str
    exchange: str


class QuotesResponse(BaseModel):
    symbols: dict[str, Quote | None]


class MacroSeriesItem(BaseModel):
    key: str
    title: str
    category: str
    unit: str
    frequency: str
    source: str
    sourceUrl: str | None = None
    latest: float | None = None
    period: str | None = None
    change: float | None = None


class BenchmarkSeriesItem(BaseModel):
    name: str
    latest: float | None = None
    change: float | None = None
    asOf: str | None = None


class BenchmarkGroup(BaseModel):
    key: str
    title: str
    unit: str
    series: list[BenchmarkSeriesItem]


class BenchmarksResponse(BaseModel):
    groups: list[BenchmarkGroup]


class KiteAuthStatus(BaseModel):
    """Non-secret Kite auth state (tokens/secrets never leave the keyring)."""

    configured: bool
    api_key_set: bool
    authenticated: bool
    user: str | None = None
    login_time: str | None = None
    expires_hint: str


class KiteLoginUrl(BaseModel):
    url: str


class KiteConnected(BaseModel):
    """Kite callback result; extra non-secret session metadata is passed through."""

    model_config = ConfigDict(extra="allow")

    status: str
    user_id: str | None = None
    user_name: str | None = None


class StatusResponse(BaseModel):
    status: str


class HealthResponse(BaseModel):
    """Liveness: the process is up and (when possible) the DB answers."""

    ok: bool
    db: str
    version: str


class ReadyResponse(BaseModel):
    """Readiness: DuckDB opens, migrations are at latest, data dir writable."""

    status: str
    db: str
    version: str


class DataQualityCheck(BaseModel):
    check_name: str
    target: str
    period: str | None = None
    severity: str
    message: str
    details: Any = None
    created_at: str


class HealthDataResponse(BaseModel):
    status: str
    checks: list[DataQualityCheck]
    summary: dict[str, int]
    asOf: str


class IngestionMetaResponse(BaseModel):
    freshness: Any
    recent_runs: Any
