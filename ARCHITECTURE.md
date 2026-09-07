# Bazzar Terminal — Architecture

## Big picture

```
Electron shell (electron/)                — secure desktop wrapper, NSIS installer
  └─ React renderer (src/)                — Vite + React 18 + Tailwind, black/gold theme
        │  HTTP/JSON + PNG over 127.0.0.1:8787
        ▼
FastAPI sidecar (backend/server.py)       — local-only API, never fabricates numbers
  ├─ backend/db.py + db_config.json       — DuckDB, config-driven bootstrap
  ├─ backend/openalgo_client.py           — market data client (provider swap → Kite in P3)
  ├─ backend/fetch_daily / fetch_indices  — checkpointed, alphabetical daily pulls
  ├─ backend/charts.py                    — matplotlib (Agg) PNG chart renderers
  └─ backend/settings.py / logging_config.py — validated config + structured logs

quant/                                    — standalone analytics library (pure functions)
  risk/ copulas/ timeseries/ portfolio/ stats/ pricing/

archive/                                  — legacy sources, reference only, never executed
```

## Data flow (daily)

1. `python -m backend.fetch_indices` / `fetch_daily` pull daily bars from the
   configured market-data provider, in strict alphabetical order, writing
   upserts + `fetch_checkpoint` rows into DuckDB (`data/bazzar.duckdb`).
2. Macro/benchmark observations land in `macro_observations` /
   `benchmark_observations` (registry: `backend/db_config.json`).
3. The renderer calls the FastAPI sidecar for JSON lists and PNG charts.
   Unsynced data returns `null` fields — the UI shows "awaiting data sync".

## Hard rules (from SPEC.md, extended)

1. **Never fabricate numbers.** Missing data ⇒ `null`/`[]`, never placeholders.
2. **DuckDB is the only store**; `db_config.json` is the single schema source.
3. **Credentials never enter git** — `.env` (gitignored) today, OS keyring in P6.
4. **Daily timeframe only** from the broker API (rate-limit respect).
5. **All renderer data via the API** (`src/api.js`); no mock data in `src/`.
6. Electron: `contextIsolation`, `sandbox`, no `nodeIntegration`, narrow
   preload IPC only.

## Repo map

| Path | What lives there |
|---|---|
| `electron/` | Main process, preload, update manifest |
| `src/` | React renderer (components, api client, theme) |
| `backend/` | FastAPI sidecar, DuckDB layer, fetchers, charts |
| `quant/` | 180-module analytics library (6 domain packages) |
| `archive/` | Legacy JSX drafts + Go scraper prototype (reference only) |
| `scripts/` | Installer build helpers (icon, payload staging, NSIS) |
| `installer/` | NSIS script + encoded icon |
| `tests/` | pytest suite (compile gates, backend imports, …) |
| `.github/` | CI workflow + Dependabot |

## Roadmap status

v2.0 execution follows `BAZZAR_ROADMAP.md` (P0 repo hygiene + P1 tooling done
in 1.3.0; P2 data-layer hardening and P3 Kite Connect migration next).
