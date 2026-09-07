# Bazzar Terminal — Architecture

## Big picture

```
Electron shell (electron/)                — secure desktop wrapper, NSIS installer
  └─ React renderer (src/)                — Vite + React 18 + Tailwind, black/gold theme
        │  HTTP/JSON + PNG over 127.0.0.1:8787
        ▼
FastAPI sidecar (backend/server.py)       — local-only API, never fabricates numbers
  ├─ backend/db.py + db_config.json       — DuckDB, config-driven bootstrap (runs migrations)
  ├─ backend/migrate.py + migrations/     — versioned schema (schema_migrations, NNNN_*.sql)
  ├─ backend/validation.py                — write-path OHLCV validation → data_rejects quarantine
  ├─ backend/calendar.py + data/          — NSE trading calendar (seeded 2025–2026 window)
  ├─ backend/ingestion.py                 — ingestion_runs audit (asOf / staleness reporting)
  ├─ backend/backup.py                    — parquet snapshots, retention 14 daily + 12 monthly
  ├─ backend/openalgo_client.py           — market data client (provider swap → Kite in P3)
  ├─ backend/fetch_daily / fetch_indices  — checkpointed, alphabetical, validated daily pulls
  ├─ backend/charts.py                    — matplotlib (Agg) PNG chart renderers
  └─ backend/settings.py / logging_config.py — validated config + structured logs

quant/                                    — standalone analytics library (pure functions)
  risk/ copulas/ timeseries/ portfolio/ stats/ pricing/

archive/                                  — legacy sources, reference only, never executed
```

## Data flow (daily)

1. `python -m backend.fetch_indices` / `fetch_daily` pull daily bars from the
   configured market-data provider, in strict alphabetical order. Every batch
   passes `backend/validation.py`: valid rows are upserted idempotently,
   invalid rows are quarantined in `data_rejects` with a reason (never
   silently dropped, never crashing the run); `fetch_checkpoint` records the
   last completed symbol so an interrupted run resumes at the next one. Each
   run is audited in `ingestion_runs` (rows written/rejected, status, error).
2. Dates are checked against the `trading_calendar` (NSE, seeded from
   `backend/data/nse_calendar.csv`; refresh annually when NSE publishes the
   next calendar). Outside the seeded coverage window the calendar check is
   skipped rather than guessed.
3. Macro/benchmark observations land in `macro_observations` /
   `benchmark_observations` (registry: `backend/db_config.json`).
4. The renderer calls the FastAPI sidecar for JSON lists and PNG charts.
   Unsynced data returns `null` fields — the UI shows "awaiting data sync".
   `/api/meta/ingestion` reports per-job freshness (`data_as_of`) and
   `/api/meta/rejects` exposes the quarantine.
5. `python -m backend.backup create` snapshots the whole database to
   timestamped parquet under `data/backups/` (retention: last 14 daily +
   12 monthly), `restore` imports a snapshot into a fresh file.

## Schema management

- `backend/migrations/NNNN_*.sql` files are applied in order at startup by
  `backend/migrate.py` and recorded in `schema_migrations`.
- `0001_init.sql` is the generated baseline of the `db_config.json` domain
  tables; `0002_ops_tables.sql` adds the operational tables (`data_rejects`,
  `ingestion_runs`, `trading_calendar`) which use sequences/defaults the
  config DDL does not express.
- Rule: never edit an applied migration — add a new `NNNN_*.sql`. When a
  domain table changes in `db_config.json`, pair it with a migration.
- `initialize_database()` = migrate to latest → config safety-net sync →
  seed reference tables and the trading calendar. Idempotent on every boot.

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

v2.0 execution follows `BAZZAR_ROADMAP.md` (P0 repo hygiene + P1 tooling in
1.3.0; P2 data-layer hardening in 1.4.0; P3 Kite Connect migration next).
