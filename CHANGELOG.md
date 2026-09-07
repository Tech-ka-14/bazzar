# Changelog

All notable changes to Bazzar Terminal. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
versioning: [SemVer](https://semver.org/).

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
