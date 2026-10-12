# Changelog

All notable changes to Bazzar Terminal. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
versioning: [SemVer](https://semver.org/).

## [1.7.0] - 2026-10-12

### Added (P5 — backend API hardening, roadmap 5.1–5.5)
- **Localhost bearer-token handshake (5.1):** the Electron main process
  generates a random 32-byte hex token per launch (`crypto.randomBytes`),
  passes it to the FastAPI sidecar via `BAZZAR_API_TOKEN`, and exposes it to
  the renderer over a new `get-api-token` IPC (`window.bazzar.getApiToken()`
  in `preload.cjs`). `src/api.js` attaches `Authorization: Bearer <token>` to
  every request. A new `BearerAuthMiddleware` returns 401 (in the standard
  error envelope) for any `/api/*` request without the matching token when
  the env var is set; unset = documented open dev fallback. Sole exemption:
  `/api/auth/kite/callback` (+ `/api/v1` twin) — the external browser is
  redirected there by kite.trade after login and cannot know the token; the
  one-time `request_token` is itself the credential.
- **CORS lockdown (5.2):** `allow_origins` is exactly the Vite dev origins
  plus `"null"` (packaged Electron `file://` pages send `Origin: null`);
  methods narrowed to GET/POST, headers to Authorization/Content-Type/
  If-None-Match. The server binds `127.0.0.1` only (unchanged, now
  documented).
- **Contract hardening (5.3):** single error envelope
  `{"error": {"code", "message"}}` via global exception handlers
  (HTTPException → snake_case status code, validation → 422
  `validation_error`, catch-all → 500 `internal_error` with server-side
  traceback logging, never leaking internals). Every request gets an
  `X-Request-ID` (uuid4, bound to structlog context). All routes now live
  under `/api/v1`; the flat `/api` mount stays as a deprecated alias for one
  release (excluded from the OpenAPI schema) and the renderer calls
  `/api/v1`. New `backend/schemas.py` holds pydantic response models wired
  as `response_model=` on the main GET endpoints (indices, home/indices,
  macro, benchmarks, search, quotes, kite auth, health/ready/health-data).
- **Performance (5.4):** `GZipMiddleware` (1KB minimum); weak body-hash
  ETags with `If-None-Match` → 304 on `/api/indices`, `/api/macro*` and
  `/api/benchmarks*`; chart PNGs are now cache-first with a data-fingerprint
  manifest under `<data dir>/cache/charts/<kind>/<key>_<paramhash>.png` +
  `manifest.json` (unchanged data → cache hit, fresh sync → re-render, the
  matplotlib generation path itself unchanged); chart rendering is capped by
  an `asyncio.Semaphore` (`BAZZAR_API_CONCURRENCY`, default 4) and moved off
  the event loop via `run_in_threadpool`.
- **Readiness & graceful shutdown (5.5):** `/api/health` stays liveness;
  new `/api/health/ready` checks DuckDB opens, migrations are at latest and
  the data dir is writable → 200 `{"status": "ready", ...}` else 503
  envelope. The sidecar logs a clean shutdown event on SIGTERM/SIGINT;
  Electron now SIGTERMs the sidecar on quit and SIGKILLs it after a 3s
  grace period.
- **Renderer:** chart `<img>` consumers fetch PNGs as authenticated blobs
  through `fetchChartObjectUrl()` (object URLs, revoked on cleanup) inside
  `ChartImage.jsx`; `KiteStatus.jsx` now goes through `apiGet` like every
  other component. `index.html` CSP `img-src` gains `blob:` for the object
  URLs.

### Tests (P5)
- New suites: `test_api_auth.py` (401/200 matrix + dev fallback + callback
  exemption), `test_api_contracts.py` (envelope shapes on 401/404/422/500,
  X-Request-ID, v1/alias equivalence, CORS allow/deny, exact response-shape
  keys), `test_api_perf.py` (ETag 200→304, gzip, warm indices p95 timing),
  `test_health_ready.py` (liveness vs readiness incl. unwritable data dir),
  `test_chart_cache.py` (manifest caching, fingerprint invalidation, per-
  param cache keys); vitest coverage for the bearer header + chart blob
  fetching in `src/__tests__/api.test.js`.

## [1.6.0] - 2026-10-12

### Added (P4-A — government / open-data source fetchers)
- **RBI DBIE source** (`backend/sources/rbi.py`): fetches Indian benchmark
  series from the RBI Database on Indian Economy gateway
  (`POST https://data.rbi.org.in/CIMS_Gateway_DBIE/GATEWAY/SERVICES/<service>`,
  guest bearer via `security_generateSessionToken`, HTML-entity-encoded JSON
  responses). G-Sec 10Y/5Y yields (`YIELD_GOV_SEC_RN`, sliced by residual
  maturity) and 91-day T-Bill yield (`YIELD_TB_RN`, 15–91 days) into
  `benchmark_observations`; weekly forex reserves (`FR_EXG_RESV_RN`, total,
  US$ million → USD bn) into `macro_observations`. Series codes, dimensions
  and parameters live in `db_config.json -> sources.rbi` (no magic IDs in
  code). Policy rates (repo / reverse repo / CRR / `rbi_repo`) are config-
  ready but skipped with a log line: DBIE carries them only in the
  "Key Rates" indicators report (id 531) behind the BOE OpenDocument
  guest-token chain — a documented P4 follow-up, never fabricated.
- **International benchmarks** (`backend/sources/intl.py`): US Treasury
  daily par yield curve CSV (tolerant of the legacy `10 Yr` and current
  `BC_10YEAR` column names) → `us_10y`; FRED `FEDFUNDS` → `us_fed_funds`
  (skipped with a clear log line when `FRED_API_KEY` is unset).
- **Benchmark upsert helper** (`backend/benchmarks.py`):
  `upsert_benchmark_observation` — idempotent ON CONFLICT upsert with
  series-key validation against `benchmark_series` (mirrors
  `backend.macro.upsert_observation`).
- Both syncs run inside `ingestion_run` (`rbi_macro` / `intl_benchmarks`)
  with per-series failure → partial status; HTTP via injectable sessions,
  TokenBucket rate limiting and tenacity backoff on 429/5xx.
- Settings: `fred_api_key` (FRED_API_KEY) and `ogd_api_key` (OGD_API_KEY,
  reserved for P4-B) — non-secret public keys, .env only (see .env.example).

### Added (P4-B — MoSPI/OGD + NSE open-data fetchers)
- **MoSPI via data.gov.in OGD** (`backend/sources/mospi.py`, roadmap 4.2):
  `GET https://api.data.gov.in/resource/{resource_id}?api-key={OGD_API_KEY}`
  for `cpi_inflation` (monthly) and `wpi_inflation` (monthly) into
  `macro_observations`. Resource IDs, field mappings and period formats
  live in `db_config.json -> sources.ogd.resources` (no magic IDs in code);
  the whole sync is skipped cleanly when `OGD_API_KEY` is unset, and
  `iip`/`gdp_growth` ship with empty resource IDs plus documented gap
  notes (no live OGD series — skipped with a log line, never fabricated).
  Tolerant pure period parser: "Jan 2025", "2025-01", "01/2025",
  "Q1 2024-25" → monthly `YYYY-MM` / quarterly `YYYY-Qn` labels.
- **NSE open data** (`backend/sources/nse_open.py`, roadmap 4.3): market
  holidays from `api/holiday-master?type=trading` upserted into
  `trading_calendar` via the new `backend.calendar.upsert_trading_days`
  helper (Muhurat special sessions stay trading days, matching the seeded
  calendar); FII/DII daily flows from `api/fiidiiTradeReact` into the new
  `fii_dii` benchmark group (`fii_net` / `dii_net`, ₹ crore); index
  constituents from `api/equity-stockIndices` cached under
  `BAZZAR_DATA_DIR/cache/nse/` (6h TTL, stale-cache fallback, `[]` on
  failure — a data-access helper for future UI, no DB table). Cookie
  bootstrap against `www.nseindia.com` with one 401/403 re-auth retry,
  TokenBucket + tenacity on 429/5xx.
- Both syncs run inside `ingestion_run` (`mospi_macro` / `nse_open`) with
  per-series/per-dataset failure → partial status; tests run fully offline
  on sanitized recorded fixtures (OGD monthly/quarterly payloads,
  holiday-master, fiidiiTradeReact, equity-stockIndices).

### Added (P4-C — reconciliation & data quality, roadmap 4.5)
- **`data_quality` table** (migration `0004_data_quality.sql`): append-only
  audit of every check result — `(check_name, target, period, severity
  ('info'|'warn'|'fail'), message, details JSON, created_at)`. Owned by
  migrations (sequence + default), same pattern as the P2 ops tables.
- **Reconciliation checks** (`backend/reconcile.py`):
  `check_kite_vs_bhavcopy` samples up to 10 stored NSE closes from the
  latest stored trading day and compares them against the official NSE
  bhavcopy (provider injectable; >0.5% diff → warn, >2× → fail, missing
  either side → info "no data to compare"); `check_macro_freshness` flags
  stale `macro_observations` per the series' configured `frequency`
  (tolerances are documented constants; never-synced → info);
  `check_benchmark_freshness` does the same for `benchmark_observations`
  per group cadence (daily groups ~7d, monthly `repo_rates` 45d).
  `run_all` executes every check inside an `ingestion_run(con,
  "reconcile")` (fail-severity findings → partial run) and returns a
  `{checks_run, info, warn, fail, status}` summary. CLI:
  `python3 -m backend.reconcile` (exit 1 on any fail-severity finding).
- **One-command seed CLI** (`backend/sources/sync_all.py`):
  `python3 -m backend.sources.sync_all` runs RBI → intl benchmarks (FRED
  skipped without a key) → MoSPI/OGD (skipped without a key) → NSE open →
  `reconcile.run_all`, prints a per-source status table plus the
  data-quality summary, and exits 1 only on hard failures — missing keys /
  offline sources are clean skips, never crashes.
- **`GET /api/health/data`**: `{status, checks, summary, asOf}` — latest
  `data_quality` row per (check_name, target); `red` when an unresolved
  fail is younger than 48h, `amber` on any current warn or older unresolved
  fail, else `green`; empty table → green with empty checks (never a 500).
- **Tests**: 30 new tests — reconcile checks with a fake bhavcopy provider,
  macro/benchmark freshness per frequency, run_all audit + CLI exit codes,
  sync_all offline fail-soft behaviour, and the health endpoint matrix
  (empty/warn/recent-fail/old-fail/resolved).

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
