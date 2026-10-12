# Changelog

All notable changes to Bazzar Terminal. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
versioning: [SemVer](https://semver.org/).

## [1.5.0] - 2026-09-07

### Added (P3 — Kite Connect integration)
- **Provider abstraction** (`backend/providers/`): a `MarketDataProvider`
  protocol (daily history, quotes, instrument master) with explicit
  `ProviderError` / `ProviderAuthRequired` / `ProviderCapabilityError`
  semantics. Fetchers are provider-agnostic; tests inject fakes.
- **Kite Connect provider** (`providers/kite.py`): primary market-data
  source. Daily-only (`interval="day"` hardcoded), historical windows chunked
  at ≤ 2000 days per call (a 10-year backfill is 2 chunks/symbol), ~2.5
  requests/second token bucket with jitter, tenacity exponential backoff on
  429/5xx/network errors, and `TokenException` → `KiteAuthRequired` with NO
  retry-loop (Kite tokens expire daily — re-authentication is a user action).
- **Kite auth flow** (`backend/kite_auth.py` + 4 API endpoints): redirect
  login (`GET /api/auth/kite/login-url`), exchange callback
  (`GET /api/auth/kite/callback`), status (`GET /api/auth/kite/status`),
  disconnect (`POST /api/auth/kite/disconnect`). The access token and
  `KITE_API_SECRET` live in the **OS keyring only** — never .env/DB/git;
  `.env` holds only the non-secret `KITE_API_KEY`. CLI:
  `python -m backend.kite_auth set-secret|status|logout`.
- **Instrument-master sync** (`backend/sync_instruments.py` + migration
  `0003_kite_instruments.sql`): `securities` gains `instrument_token`,
  `lot_size`, `tick_size`; sync upserts the NSE/BSE master (index segment →
  `*_INDEX` exchanges), deactivates — never deletes — vanished listings, and
  refuses to deactivate anything on an empty dump. Audited via
  `ingestion_runs` (job `instrument_sync`).
- **NSE bhavcopy fallback provider** (`providers/nse_bhavcopy.py`): official
  NSE archive CSVs, polite headers, backoff on 429/5xx, 404 = holiday.
  EOD-only (no quotes/instruments — raises `ProviderCapabilityError`).
- **Renderer**: `KiteStatus` pill in the topbar (polls status every 30s;
  "Connect Kite" opens the login URL in the system browser via a new
  allowlisted `shell:open-external` IPC — https + kite.trade hosts only).
- **Tests**: 41 new tests — provider protocol, chunking, retry/auth mapping,
  keyring auth store, auth endpoints, instrument sync, provider-flag fetch
  semantics (partial vs failed runs), bhavcopy parsing.

### Changed
- `fetch_daily` / `fetch_indices` accept `--provider {kite,openalgo,nse_bhavcopy}`
  (default: `MARKET_DATA_PROVIDER` setting, `openalgo`). Per-symbol failures
  skip the symbol, advance the checkpoint, and finish the run as **partial**
  (new `ingestion_runs` status); auth failures abort with exit code 3.
- `backend/openalgo_client.py` is now a compatibility shim re-exporting from
  `backend/providers/openalgo.py`.

## [1.4.0] - 2026-09-07

### Added (P2 — data layer hardening)
- **Schema versioning**: `schema_migrations` table + `backend/migrate.py`
  runner applying `backend/migrations/NNNN_*.sql` in order inside
  transactions. `0001_init.sql` = generated baseline of the config domain
  tables; `0002_ops_tables.sql` = operational tables. `initialize_database()`
  is now "migrate to latest → config sync → seed".
- **Write-path validation** (`backend/validation.py`): every OHLCV upsert is
  validated (positive prices, `high >= low`, `low <= open/close <= high`,
  `volume >= 0`, no future dates, no duplicate batch keys, trading-calendar
  alignment inside the seeded coverage window). Invalid rows are quarantined
  into `data_rejects` with job/table/payload/reason — never silently dropped,
  never crashing a run.
- **Trading calendar** (`backend/calendar.py` + `backend/data/nse_calendar.csv`):
  NSE calendar seeded for 2025–2026 (holidays from NSE circulars 170/2024 and
  172/2025 + 03/2026; Union Budget Saturday 2025-02-01 and Muhurat sessions
  2025-10-21 / 2026-11-08 marked as trading days). `is_trading_day` returns
  `None` outside coverage so historical data is never rejected on a guess.
- **Ingestion audit** (`backend/ingestion.py`): `ingestion_runs` records every
  fetch job (started/finished, rows written/rejected, status, error);
  `data_freshness()` reports per-job `data_as_of` for staleness badges.
- **Backups** (`backend/backup.py`): `python -m backend.backup create` exports
  timestamped parquet snapshots to `data/backups/` with retention (14 daily +
  12 monthly); `restore` imports a snapshot into a fresh database file.
- **API**: `GET /api/meta/ingestion` (freshness + recent runs) and
  `GET /api/meta/rejects` (quarantine inspection).
- **Tests**: 49 new tests — migrations idempotency, validation rules,
  calendar semantics, ingestion audit, checkpoint resume, and a
  backup→restore round-trip asserting byte-identical per-table row counts.

### Changed
- `fetch_daily` / `fetch_indices` write through the validated upsert path and
  run inside an `ingestion_run` audit wrapper; checkpoint discipline
  unchanged (strict alphabetical, resume-after-checkpoint).

## [1.3.0] - 2026-09-07

### Changed (P0 — repository hygiene)
- Reorganized the 180 loose root-level Python quant modules into the `quant/`
  package with six domain subpackages: `risk`, `copulas`, `timeseries`,
  `portfolio`, `stats`, `pricing`. No logic changes.
- Moved original root-level React components to `archive/frontend-legacy/`
  (the repaired, supported versions live in `src/components/`).
- Moved the Go/Fyne scraper prototype (`main.go`, `commodity_scarp.go`,
  `go.mod`) to `archive/go-scraper/`; it remains source-only reference.
- Renamed `John_Techincal.py` → `quant/timeseries/john_technical.py` (typo).
- Renamed `copula_monte_carloo_var.py` →
  `quant/copulas/copula_monte_carlo_t_marginals.py` (typo; distinct module,
  not a duplicate).
- Moved `ChartDashboard.py` (early draft of `FundamentalAnalyzer`) to
  `archive/frontend-legacy/`.
- Removed the stray 1-byte `quant` placeholder file.

### Added (P1 — engineering foundation)
- `pyproject.toml` with project metadata, ruff (lint+format), mypy, and
  pytest configuration.
- `requirements-dev.txt` (pytest, ruff, mypy, pre-commit, …) and expanded
  runtime `requirements.txt` (pydantic, pydantic-settings, structlog,
  tenacity).
- Pre-commit hooks: ruff, ruff-format, trailing whitespace, YAML check,
  gitleaks (secret scanning).
- GitHub Actions CI (`.github/workflows/ci.yml`): Python gate
  (ruff, ruff format, mypy, pytest) + Node gate (eslint, prettier check,
  vitest, vite build) + gitleaks scan.
- Dependabot for pip, npm, and GitHub Actions.
- `backend/settings.py` — single validated configuration object
  (pydantic-settings), fails fast on bad config.
- `backend/logging_config.py` — structured JSON logging (structlog),
  rotating file under `data/logs/`.
- ESLint 9 flat config + Prettier + Vitest for the JS side; `npm run check`
  runs the full JS gate.
- `tests/` — compile gate for every module in `quant/` and `backend/`,
  backend import smoke test.
- `Makefile` with `make check` / `make setup` / `make dev` entry points.
- `ARCHITECTURE.md`, this changelog, and `archive/README.md`.

[1.3.0]: https://github.com/Tech-ka-14/bazzar/compare/v1.2.0...v1.3.0
