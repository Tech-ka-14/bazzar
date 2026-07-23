"""FastAPI local server for the Bazzar Terminal data layer.

Implements the SPEC "Local HTTP API contract" (base http://127.0.0.1:8787,
port overridable via BAZZAR_API_PORT). Run with:

    python3 -m backend.server

CRITICAL: numbers are never fabricated. When a table has no data yet,
endpoints return null fields / empty lists so the UI can show an
"awaiting data sync" state; chart.png endpoints return a 404 JSON error.
"""

from __future__ import annotations

import os
import re
from contextlib import contextmanager
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .charts import chart_cache_dir, render_candles_png, render_line_png
from .db import get_connection, get_db_path, initialize_database, load_config
from .fetch_indices import ensure_snapshot_view

VERSION = "1.2.0"

app = FastAPI(title="Bazzar Terminal Data API", version=VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local desktop app
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    initialize_database()
    with db() as con:
        ensure_snapshot_view(con)


@contextmanager
def db():
    con = get_connection()
    try:
        yield con
    finally:
        con.close()


# --- helpers ---------------------------------------------------------------

def _rows_to_bars(rows) -> list[dict[str, Any]]:
    return [{"date": str(r[0])[:10], "open": r[1], "high": r[2], "low": r[3],
             "close": r[4], "volume": r[5] if len(r) > 5 else None} for r in rows]


def _index_bars(con, symbol: str) -> list[dict[str, Any]]:
    rows = con.execute(
        "SELECT date, open, high, low, close FROM index_daily"
        " WHERE symbol = ? ORDER BY date", (symbol,)
    ).fetchall()
    return _rows_to_bars(rows)


def _stock_bars(con, symbol: str, exchange: Optional[str]) -> list[dict[str, Any]]:
    if exchange:
        rows = con.execute(
            "SELECT date, open, high, low, close, volume FROM daily_ohlcv"
            " WHERE symbol = ? AND exchange = ? ORDER BY date", (symbol, exchange)
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT date, open, high, low, close, volume FROM daily_ohlcv"
            " WHERE symbol = ? ORDER BY date", (symbol,)
        ).fetchall()
    return _rows_to_bars(rows)


def _latest_quote(con, symbol: str, exchange: Optional[str]) -> Optional[dict[str, Any]]:
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
    change_pct = (round(change / prev_close * 100, 4)
                  if prev_close not in (None, 0) else None)
    return {"value": last["close"], "change": change,
            "changePct": change_pct, "asOf": last["date"]}


def _sanitize(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name)


# --- endpoints ---------------------------------------------------------------

@app.get("/api/health")
def health() -> dict[str, Any]:
    db_path = get_db_path()
    ok = db_path.exists()
    if ok:
        try:
            with db() as con:
                con.execute("SELECT 1")
        except Exception:
            ok = False
    return {"ok": ok, "db": str(db_path), "version": VERSION}


@app.get("/api/home/indices")
def home_indices() -> list[dict[str, Any]]:
    config = load_config()
    out = []
    with db() as con:
        for entry in config["home_indices"]:
            quote = _latest_quote(con, entry["symbol"], entry["exchange"]) or {}
            out.append({
                "name": entry["name"],
                "symbol": entry["symbol"],
                "value": quote.get("value"),
                "change": quote.get("change"),
                "changePct": quote.get("changePct"),
                "asOf": quote.get("asOf"),
            })
    return out


@app.get("/api/indices")
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
    return [{
        "symbol": r[0], "name": r[1], "exchange": r[2],
        "open": r[3], "high": r[4], "low": r[5], "close": r[6],
        "yearHigh": r[7], "yearLow": r[8],
        "asOf": str(r[9])[:10] if r[9] is not None else None,
    } for r in rows]


@app.get("/api/indices/{symbol}/chart.png")
def index_chart(symbol: str) -> FileResponse:
    with db() as con:
        bars = _index_bars(con, symbol)
        if not bars:
            row = con.execute(
                "SELECT symbol FROM index_master WHERE upper(symbol) = upper(?)",
                (symbol,),
            ).fetchone()
            if row:
                bars = _index_bars(con, row[0])
                symbol = row[0]
    if not bars:
        raise HTTPException(status_code=404,
                            detail=f"no daily data synced for index '{symbol}'")
    out = chart_cache_dir() / f"index_{_sanitize(symbol)}.png"
    render_candles_png(bars, f"{symbol} — daily", str(out))
    return FileResponse(str(out), media_type="image/png")


@app.get("/api/stocks/{symbol}/chart.png")
def stock_chart(symbol: str, exchange: str = Query(default="NSE")) -> FileResponse:
    with db() as con:
        bars = _stock_bars(con, symbol, exchange)
        if not bars:
            bars = _stock_bars(con, symbol, None)
    if not bars:
        raise HTTPException(
            status_code=404,
            detail=f"no daily data synced for stock '{symbol}' ({exchange})")
    out = chart_cache_dir() / f"stock_{_sanitize(exchange)}_{_sanitize(symbol)}.png"
    render_candles_png(bars, f"{symbol} ({exchange}) — daily", str(out))
    return FileResponse(str(out), media_type="image/png")


@app.get("/api/search")
def search(q: str = Query(default=""), limit: int = Query(default=10, ge=1, le=100)
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

    def rank(symbol: str, name: str) -> Optional[int]:
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
    return [{"symbol": s, "name": n, "exchange": e}
            for _, s, n, e in scored[:limit]]


@app.get("/api/quotes")
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


@app.get("/api/benchmarks")
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
                change = (round(rows[0][1] - rows[1][1], 4)
                          if len(rows) > 1 else None)
                as_of = str(rows[0][0])[:10] if rows else None
                series_out.append({"name": series["name"], "latest": latest,
                                   "change": change, "asOf": as_of})
            groups.append({"key": group["key"], "title": group["title"],
                           "unit": group["unit"], "series": series_out})
    return {"groups": groups}


@app.get("/api/benchmarks/{key}/chart.png")
def benchmark_chart(key: str) -> FileResponse:
    config = load_config()
    group = next((g for g in config["benchmarks"] if g["key"] == key), None)
    if group is None:
        raise HTTPException(status_code=404, detail=f"unknown benchmark group '{key}'")
    series_points = []
    labels = []
    with db() as con:
        for series in group["series"]:
            rows = con.execute(
                "SELECT date, value FROM benchmark_observations"
                " WHERE series_key = ? ORDER BY date", (series["key"],)
            ).fetchall()
            if rows:
                series_points.append([(str(r[0])[:10], r[1]) for r in rows])
                labels.append(series["name"])
    if not series_points:
        raise HTTPException(status_code=404,
                            detail=f"no observations synced for benchmark '{key}'")
    out = chart_cache_dir() / f"benchmark_{_sanitize(key)}.png"
    render_line_png(series_points, group["title"], group["unit"], str(out),
                    series_labels=labels)
    return FileResponse(str(out), media_type="image/png")


@app.get("/api/macro")
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
        change = (round(latest - prev, 4)
                  if latest is not None and prev is not None else None)
        out.append({
            "key": key, "title": title, "category": category, "unit": unit,
            "frequency": frequency, "source": source, "sourceUrl": source_url,
            "latest": latest, "period": period, "change": change,
        })
    return out


def main() -> None:
    import uvicorn

    port = int(os.environ.get("BAZZAR_API_PORT", "8787"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
