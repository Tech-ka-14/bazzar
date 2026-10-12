"""FastAPI local server for the Bazzar Terminal data layer.

Implements the SPEC "Local HTTP API contract" (base http://127.0.0.1:8787,
port overridable via BAZZAR_API_PORT). Run with:

    python3 -m backend.server

P5 (roadmap 5.1–5.5) hardening:
  * bearer-token auth on /api/* when BAZZAR_API_TOKEN is set (Electron
    passes a per-launch token; unset = documented dev fallback)
  * CORS locked to the Vite dev origins (+ "null" for packaged file://)
  * single error envelope, X-Request-ID on every response
  * routes live under /api/v1, with a deprecated /api alias for one release
  * pydantic response models (backend/schemas.py), gzip, weak ETags,
    manifest-cached chart PNGs, a concurrency semaphore on chart rendering
  * /api/health (liveness) vs /api/health/ready (readiness)

CRITICAL: numbers are never fabricated. When a table has no data yet,
endpoints return null fields / empty lists so the UI can show an
"awaiting data sync" state; chart.png endpoints return a 404 JSON error.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import os
import re
from contextlib import contextmanager
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import schemas
from .charts import cached_chart_png, render_candles_png, render_line_png
from .db import get_connection, get_data_dir, get_db_path, initialize_database, load_config
from .fetch_indices import ensure_snapshot_view
from .middleware import (
    BearerAuthMiddleware,
    RequestIDMiddleware,
    WeakETagMiddleware,
    error_envelope,
)
from .settings import get_settings

VERSION = "1.7.0"

app = FastAPI(title="Bazzar Terminal Data API", version=VERSION)

# Middleware stack (added innermost → outermost). Request path:
#   CORS → X-Request-ID → bearer auth → weak ETag → gzip → route
# CORS is outermost so unauthenticated preflight (OPTIONS) still answers.
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(WeakETagMiddleware)
app.add_middleware(BearerAuthMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    # Vite dev server origins; "null" is the Origin sent by the packaged
    # Electron renderer (file:// pages) — a loopback desktop app has no
    # meaningful web origin, and the bearer token is the real gate.
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "null"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "If-None-Match"],
)


@app.on_event("startup")
def _startup() -> None:
    initialize_database()
    with db() as con:
        ensure_snapshot_view(con)
    app.state.chart_semaphore = asyncio.Semaphore(get_settings().bazzar_api_concurrency)


@app.on_event("shutdown")
def _shutdown() -> None:
    """Graceful shutdown: DuckDB connections are per-request (opened and
    closed inside each endpoint), so there is no long-lived handle to close;
    log the transition so sidecar logs show a clean SIGTERM/SIGINT story."""
    from .logging_config import get_logger

    get_logger("backend.server").info("server shutdown complete", version=VERSION)


def _chart_semaphore() -> asyncio.Semaphore:
    """Concurrency cap for chart rendering (default 4; BAZZAR_API_CONCURRENCY)."""
    sem = getattr(app.state, "chart_semaphore", None)
    if sem is None:  # startup not run (direct TestClient use) — create lazily
        sem = asyncio.Semaphore(get_settings().bazzar_api_concurrency)
        app.state.chart_semaphore = sem
    return sem


# --- error envelope (P5, roadmap 5.3) ----------------------------------------


def _status_code_name(status_code: int) -> str:
    try:
        phrase = HTTPStatus(status_code).phrase
    except ValueError:
        return "http_error"
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", phrase.lower())).strip("_")


@app.exception_handler(StarletteHTTPException)
async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail: Any = exc.detail
    message = detail if isinstance(detail, str) and detail else _status_code_name(exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_envelope(_status_code_name(exc.status_code), message),
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    message = "request validation failed"
    if errors:
        first = errors[0]
        loc = ".".join(str(part) for part in first.get("loc", []))
        message = f"request validation failed ({loc}: {first.get('msg', 'invalid')})"
    return JSONResponse(status_code=422, content=error_envelope("validation_error", message))


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all: log the traceback server-side, never leak internals."""
    from .logging_config import get_logger

    request_id = getattr(request.state, "request_id", "-")
    get_logger("backend.server").error(
        "unhandled exception",
        error_type=exc.__class__.__name__,
        request_id=request_id,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content=error_envelope(
            "internal_error", f"internal server error (request id {request_id})"
        ),
    )


@contextmanager
def db():
    con = get_connection()
    try:
        yield con
    finally:
        con.close()


# --- helpers ---------------------------------------------------------------


def _rows_to_bars(rows) -> list[dict[str, Any]]:
    return [
        {
            "date": str(r[0])[:10],
            "open": r[1],
            "high": r[2],
            "low": r[3],
            "close": r[4],
            "volume": r[5] if len(r) > 5 else None,
        }
        for r in rows
    ]


def _index_bars(con, symbol: str) -> list[dict[str, Any]]:
    rows = con.execute(
        "SELECT date, open, high, low, close FROM index_daily WHERE symbol = ? ORDER BY date",
        (symbol,),
    ).fetchall()
    return _rows_to_bars(rows)


def _stock_bars(con, symbol: str, exchange: str | None) -> list[dict[str, Any]]:
    if exchange:
        rows = con.execute(
            "SELECT date, open, high, low, close, volume FROM daily_ohlcv"
            " WHERE symbol = ? AND exchange = ? ORDER BY date",
            (symbol, exchange),
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT date, open, high, low, close, volume FROM daily_ohlcv"
            " WHERE symbol = ? ORDER BY date",
            (symbol,),
        ).fetchall()
    return _rows_to_bars(rows)


def _latest_quote(con, symbol: str, exchange: str | None) -> dict[str, Any] | None:
    """Latest close + pointwise/% change from the last two stored bars.

    Index symbols (exchange ends with _INDEX) read index_daily; anything else
    reads daily_ohlcv. Returns None when no data has been synced yet.
    """
    if exchange and exchange.endswith("_INDEX"):
        bars = _index_bars(con, symbol)
        if not bars:  # fall back to equity table just in case
            bars = _stock_bars(con, symbol, None)
    else:
        bars = _stock_bars(con, symbol, exchange)
        if not bars:
            bars = _index_bars(con, symbol)
    if not bars:
        return None
    last = bars[-1]
    prev_close = bars[-2]["close"] if len(bars) > 1 else None
    change = round(last["close"] - prev_close, 4) if prev_close is not None else None
    change_pct = round(change / prev_close * 100, 4) if prev_close not in (None, 0) else None
    return {"value": last["close"], "change": change, "changePct": change_pct, "asOf": last["date"]}


def _bars_fingerprint(bars: list[dict[str, Any]]) -> str:
    """Cache key component describing exactly the data a chart renders."""
    last = bars[-1]
    return f"{len(bars)}:{last['date']}:{last['close']}"


# --- endpoints (mounted at /api/v1, plus a deprecated /api alias) -------------

router = APIRouter()


@router.get("/auth/kite/login-url", response_model=schemas.KiteLoginUrl)
def kite_login_url() -> dict[str, Any]:
    """The Zerodha redirect-login URL for the configured KITE_API_KEY (P3)."""
    from .providers.kite import login_url

    api_key = get_settings().kite_api_key
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="KITE_API_KEY is not configured — set it in .env first.",
        )
    return {"url": login_url(api_key)}


@router.get("/auth/kite/callback", response_model=schemas.KiteConnected)
def kite_callback(request_token: str = Query(default="")) -> dict[str, Any]:
    """Kite redirect target: exchanges request_token for a session (keyring).

    This path is exempt from the bearer-token middleware: the *external*
    browser is redirected here by kite.trade after login and cannot know the
    per-launch token; the one-time request_token is itself the credential.
    """
    from . import kite_auth
    from .providers.base import ProviderError

    if not request_token:
        raise HTTPException(status_code=400, detail="missing request_token")
    api_key = get_settings().kite_api_key
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="KITE_API_KEY is not configured — set it in .env first.",
        )
    try:
        meta = kite_auth.exchange_request_token(api_key, request_token)
    except ProviderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "connected", **meta}


@router.get("/auth/kite/status", response_model=schemas.KiteAuthStatus)
def kite_status() -> dict[str, Any]:
    """Non-secret Kite auth state for the UI (tokens never leave the keyring)."""
    from . import kite_auth

    return kite_auth.auth_status(get_settings().kite_api_key)


@router.post("/auth/kite/disconnect", response_model=schemas.StatusResponse)
def kite_disconnect() -> dict[str, Any]:
    """Clear the Kite session from the keyring (the API secret is kept)."""
    from . import kite_auth

    kite_auth.clear_session()
    return {"status": "disconnected"}


@router.get("/health", response_model=schemas.HealthResponse)
def health() -> dict[str, Any]:
    """Liveness: 200 whenever the process is serving (DB check best-effort)."""
    db_path = get_db_path()
    ok = db_path.exists()
    if ok:
        try:
            with db() as con:
                con.execute("SELECT 1")
        except Exception:
            ok = False
    return {"ok": ok, "db": str(db_path), "version": VERSION}


@router.get("/health/ready", response_model=schemas.ReadyResponse)
def health_ready() -> dict[str, Any]:
    """Readiness: DuckDB opens, migrations are at latest, data dir writable.

    200 {"status": "ready", ...} when all checks pass, else 503 in the
    standard error envelope. Used by the Electron shell to know the sidecar
    can actually serve data (vs merely being alive — see /health).
    """
    from .migrate import migration_status

    problems: list[str] = []
    data_dir = get_data_dir()
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        probe = data_dir / ".ready-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except Exception:
        problems.append("data directory is not writable")
    try:
        with db() as con:
            con.execute("SELECT 1")
            pending = [m for m in migration_status(con) if not m["applied"]]
            if pending:
                names = ", ".join(str(m["name"]) for m in pending)
                problems.append(f"schema migrations pending: {names}")
    except Exception:
        problems.append("DuckDB is not available")
    if problems:
        raise HTTPException(status_code=503, detail="not ready: " + "; ".join(problems))
    return {"status": "ready", "db": str(get_db_path()), "version": VERSION}


@router.get("/health/data", response_model=schemas.HealthDataResponse)
def health_data() -> dict[str, Any]:
    """Data-quality status from the ``data_quality`` audit table (P4-C).

    Returns the latest row per (check_name, target) plus severity counts.
    Status: "red" when any unresolved fail-severity row is younger than 48h,
    "amber" when a fail is older than 48h or any warn-severity row is
    current, else "green". An empty/never-checked table is green with empty
    checks — never a 500, never a fabricated status.
    """
    cutoff = dt.datetime.now(dt.UTC).replace(tzinfo=None) - dt.timedelta(hours=48)
    with db() as con:
        try:
            rows = con.execute(
                """
                SELECT check_name, target, period, severity, message, details, created_at
                FROM data_quality
                QUALIFY ROW_NUMBER() OVER (
                    PARTITION BY check_name, target ORDER BY id DESC
                ) = 1
                ORDER BY check_name, target
                """
            ).fetchall()
        except Exception:  # table missing (pre-migration db) — green/empty
            rows = []

    checks = []
    summary = {"info": 0, "warn": 0, "fail": 0}
    recent_fail = False
    stale_fail = False
    warn = False
    for check_name, target, period, severity, message, details, created_at in rows:
        if severity in summary:
            summary[severity] += 1
        created = (
            created_at
            if isinstance(created_at, dt.datetime)
            else dt.datetime.fromisoformat(str(created_at))
        )
        if severity == "fail":
            if created >= cutoff:
                recent_fail = True
            else:
                stale_fail = True
        elif severity == "warn":
            warn = True
        parsed_details: Any = details
        if isinstance(details, str):
            try:
                parsed_details = json.loads(details)
            except ValueError:
                parsed_details = details
        checks.append(
            {
                "check_name": check_name,
                "target": target,
                "period": period,
                "severity": severity,
                "message": message,
                "details": parsed_details,
                "created_at": created.isoformat(),
            }
        )

    status = "green"
    if warn or stale_fail:
        status = "amber"
    if recent_fail:
        status = "red"
    return {
        "status": status,
        "checks": checks,
        "summary": summary,
        "asOf": dt.datetime.now(dt.UTC).isoformat(),
    }


@router.get("/meta/ingestion")
def meta_ingestion() -> dict[str, Any]:
    """Ingestion audit: per-job freshness (asOf) + recent runs (P2).

    Never fabricated: jobs that have never run simply do not appear, and
    data_as_of is null until real data has been synced.
    """
    from .ingestion import data_freshness, latest_runs

    with db() as con:
        return {"freshness": data_freshness(con), "recent_runs": latest_runs(con, limit=20)}


@router.get("/meta/rejects")
def meta_rejects(limit: int = Query(default=100, ge=1, le=1000)) -> list[dict[str, Any]]:
    """Rows quarantined by write validation (P2), newest first."""
    with db() as con:
        rows = con.execute(
            "SELECT id, job, table_name, payload, reason, rejected_at"
            " FROM data_rejects ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {
            "id": r[0],
            "job": r[1],
            "table": r[2],
            "payload": r[3],
            "reason": r[4],
            "rejected_at": str(r[5]),
        }
        for r in rows
    ]


@router.get("/home/indices", response_model=list[schemas.HomeIndex])
def home_indices() -> list[dict[str, Any]]:
    config = load_config()
    out = []
    with db() as con:
        for entry in config["home_indices"]:
            quote = _latest_quote(con, entry["symbol"], entry["exchange"]) or {}
            out.append(
                {
                    "name": entry["name"],
                    "symbol": entry["symbol"],
                    "value": quote.get("value"),
                    "change": quote.get("change"),
                    "changePct": quote.get("changePct"),
                    "asOf": quote.get("asOf"),
                }
            )
    return out


@router.get("/indices", response_model=list[schemas.IndexRow])
def indices() -> list[dict[str, Any]]:
    with db() as con:
        try:
            rows = con.execute(
                """
                SELECT m.symbol, m.name, m.exchange,
                       s.open, s.high, s.low, s.close,
                       s.year_high, s.year_low, s.as_of
                FROM index_master m
                LEFT JOIN index_snapshot s ON s.symbol = m.symbol
                ORDER BY m.sort_order
                """
            ).fetchall()
        except Exception:
            rows = con.execute(
                "SELECT symbol, name, exchange, NULL, NULL, NULL, NULL, NULL, NULL, NULL"
                " FROM index_master ORDER BY sort_order"
            ).fetchall()
    return [
        {
            "symbol": r[0],
            "name": r[1],
            "exchange": r[2],
            "open": r[3],
            "high": r[4],
            "low": r[5],
            "close": r[6],
            "yearHigh": r[7],
            "yearLow": r[8],
            "asOf": str(r[9])[:10] if r[9] is not None else None,
        }
        for r in rows
    ]


def _index_chart_data(symbol: str) -> tuple[str, list[dict[str, Any]]]:
    with db() as con:
        bars = _index_bars(con, symbol)
        if not bars:
            row = con.execute(
                "SELECT symbol FROM index_master WHERE upper(symbol) = upper(?)",
                (symbol,),
            ).fetchone()
            if row:
                symbol = row[0]
                bars = _index_bars(con, symbol)
    return symbol, bars


@router.get("/indices/{symbol}/chart.png")
async def index_chart(symbol: str) -> FileResponse:
    resolved, bars = await run_in_threadpool(_index_chart_data, symbol)
    if not bars:
        raise HTTPException(status_code=404, detail=f"no daily data synced for index '{symbol}'")
    fingerprint = _bars_fingerprint(bars)
    title = f"{resolved} — daily"
    async with _chart_semaphore():
        out = await run_in_threadpool(
            lambda: cached_chart_png(
                "index",
                resolved,
                {},
                fingerprint,
                lambda path: render_candles_png(bars, title, str(path)),
            )
        )
    return FileResponse(str(out), media_type="image/png")


def _stock_chart_data(symbol: str, exchange: str | None) -> list[dict[str, Any]]:
    with db() as con:
        bars = _stock_bars(con, symbol, exchange)
        if not bars:
            bars = _stock_bars(con, symbol, None)
    return bars


@router.get("/stocks/{symbol}/chart.png")
async def stock_chart(symbol: str, exchange: str = Query(default="NSE")) -> FileResponse:
    bars = await run_in_threadpool(_stock_chart_data, symbol, exchange)
    if not bars:
        raise HTTPException(
            status_code=404, detail=f"no daily data synced for stock '{symbol}' ({exchange})"
        )
    fingerprint = _bars_fingerprint(bars)
    title = f"{symbol} ({exchange}) — daily"
    params = {"exchange": exchange}
    async with _chart_semaphore():
        out = await run_in_threadpool(
            lambda: cached_chart_png(
                "stock",
                symbol,
                params,
                fingerprint,
                lambda path: render_candles_png(bars, title, str(path)),
            )
        )
    return FileResponse(str(out), media_type="image/png")


@router.get("/search", response_model=list[schemas.SearchResult])
def search(
    q: str = Query(default=""), limit: int = Query(default=10, ge=1, le=100)
) -> list[dict[str, Any]]:
    """Dictionary-method search: case-insensitive prefix matches first, then
    substring, then token matches, ranked; over the securities dictionary
    table, falling back to index_master names too."""
    query = q.strip().lower()
    if not query:
        return []
    with db() as con:
        dictionary = con.execute(
            "SELECT symbol, name, exchange FROM securities WHERE active"
        ).fetchall()
        dictionary += con.execute(
            "SELECT symbol, name, exchange FROM index_master WHERE active"
        ).fetchall()

    def rank(symbol: str, name: str) -> int | None:
        s, n = symbol.lower(), name.lower()
        if s.startswith(query) or n.startswith(query):
            return 0
        if query in s or query in n:
            return 1
        tokens = re.split(r"[^a-z0-9]+", n)
        if any(t.startswith(query) for t in tokens if t):
            return 2
        return None

    scored = []
    for symbol, name, exchange in dictionary:
        r = rank(symbol, name)
        if r is not None:
            scored.append((r, symbol, name, exchange))
    scored.sort(key=lambda t: (t[0], t[1]))
    return [{"symbol": s, "name": n, "exchange": e} for _, s, n, e in scored[:limit]]


@router.get("/quotes", response_model=schemas.QuotesResponse)
def quotes(symbols: str = Query(default="")) -> dict[str, Any]:
    requested = [s.strip() for s in symbols.split(",") if s.strip()]
    result: dict[str, Any] = {}
    with db() as con:
        for sym in requested:
            row = con.execute(
                "SELECT exchange FROM securities WHERE symbol = ? LIMIT 1", (sym,)
            ).fetchone()
            idx = con.execute(
                "SELECT exchange FROM index_master WHERE symbol = ? LIMIT 1", (sym,)
            ).fetchone()
            exchange = row[0] if row else (idx[0] if idx else None)
            result[sym] = _latest_quote(con, sym, exchange)
    return {"symbols": result}


@router.get("/benchmarks", response_model=schemas.BenchmarksResponse)
def benchmarks() -> dict[str, Any]:
    config = load_config()
    groups = []
    with db() as con:
        for group in config["benchmarks"]:
            series_out = []
            for series in group["series"]:
                rows = con.execute(
                    "SELECT date, value FROM benchmark_observations"
                    " WHERE series_key = ? ORDER BY date DESC LIMIT 2",
                    (series["key"],),
                ).fetchall()
                latest = rows[0][1] if rows else None
                change = round(rows[0][1] - rows[1][1], 4) if len(rows) > 1 else None
                as_of = str(rows[0][0])[:10] if rows else None
                series_out.append(
                    {"name": series["name"], "latest": latest, "change": change, "asOf": as_of}
                )
            groups.append(
                {
                    "key": group["key"],
                    "title": group["title"],
                    "unit": group["unit"],
                    "series": series_out,
                }
            )
    return {"groups": groups}


def _benchmark_chart_data(key: str) -> tuple[dict[str, Any], list, list[str]]:
    config = load_config()
    group = next((g for g in config["benchmarks"] if g["key"] == key), None)
    if group is None:
        raise HTTPException(status_code=404, detail=f"unknown benchmark group '{key}'")
    series_points = []
    labels = []
    with db() as con:
        for series in group["series"]:
            rows = con.execute(
                "SELECT date, value FROM benchmark_observations WHERE series_key = ? ORDER BY date",
                (series["key"],),
            ).fetchall()
            if rows:
                series_points.append([(str(r[0])[:10], r[1]) for r in rows])
                labels.append(series["name"])
    return group, series_points, labels


@router.get("/benchmarks/{key}/chart.png")
async def benchmark_chart(key: str) -> FileResponse:
    group, series_points, labels = await run_in_threadpool(_benchmark_chart_data, key)
    if not series_points:
        raise HTTPException(status_code=404, detail=f"no observations synced for benchmark '{key}'")
    fingerprint = json.dumps([[len(s), s[-1]] for s in series_points], default=str)
    title, unit = group["title"], group["unit"]
    async with _chart_semaphore():
        out = await run_in_threadpool(
            lambda: cached_chart_png(
                "benchmark",
                key,
                {},
                fingerprint,
                lambda path: render_line_png(
                    series_points, title, unit, str(path), series_labels=labels
                ),
            )
        )
    return FileResponse(str(out), media_type="image/png")


@router.get("/macro", response_model=list[schemas.MacroSeriesItem])
def macro() -> list[dict[str, Any]]:
    with db() as con:
        rows = con.execute(
            """
            WITH ranked AS (
                SELECT series_key, period, value,
                       ROW_NUMBER() OVER (PARTITION BY series_key ORDER BY period DESC) AS rn
                FROM macro_observations
            )
            SELECT s.key, s.title, s.category, s.unit, s.frequency, s.source,
                   s.source_url, cur.value, cur.period, prev.value
            FROM macro_series s
            LEFT JOIN ranked cur ON cur.series_key = s.key AND cur.rn = 1
            LEFT JOIN ranked prev ON prev.series_key = s.key AND prev.rn = 2
            ORDER BY s.category, s.key
            """
        ).fetchall()
    out = []
    for key, title, category, unit, frequency, source, source_url, latest, period, prev in rows:
        change = round(latest - prev, 4) if latest is not None and prev is not None else None
        out.append(
            {
                "key": key,
                "title": title,
                "category": category,
                "unit": unit,
                "frequency": frequency,
                "source": source,
                "sourceUrl": source_url,
                "latest": latest,
                "period": period,
                "change": change,
            }
        )
    return out


# Current versioned mount + one-release backward-compat alias (P5, roadmap
# 5.3): the renderer calls /api/v1; the /api alias stays (undocumented in the
# OpenAPI schema) until the next release so older shells keep working.
app.include_router(router, prefix="/api/v1")
app.include_router(router, prefix="/api", include_in_schema=False)


def main() -> None:
    import uvicorn

    port = int(os.environ.get("BAZZAR_API_PORT", "8787"))
    # Loopback-only bind: the sidecar must never be reachable off-machine.
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
