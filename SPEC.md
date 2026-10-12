# Bazzar Desktop Installer Specification

## Product definition
The repository is a flat collection of React financial-terminal components, two Go/Fyne scraper prototypes, and 180 standalone Python quant modules. It has no runnable top-level application or dependency manifests. For installation purposes, the shippable product is defined as **Bazzar Terminal**, a Windows desktop application built from the React financial-terminal UI.

## Runtime architecture
- **Desktop shell:** Electron (`electron/main.cjs`) opens the production renderer from `dist/index.html` and exposes only a narrow, context-isolated preload API.
- **Renderer:** Vite + React + Tailwind CSS. Existing repository components are moved under `src/components/` and repaired with explicit imports/exports.
- **Bundled repository payload:** Every original source file (Python, Go, JSX, docs, manifests) is included under the installed app's `resources/repository/` directory via electron-builder `extraResources`.
- **Python payload:** `requirements.txt` captures the Python modules' third-party dependencies. The desktop app does not silently execute 180 unrelated scripts; the installer ships them as source resources for audit/development use.
- **Go payload:** `go.mod` documents the scraper dependencies. The scraper remains source-only because `main.go` still points to a placeholder URL.

## Scraper test-bench contract
- Add a dedicated **Scraper** tab to the desktop navigation.
- The original Go/Fyne scraper remains source-only because it is not wired to the Electron app and still contains placeholder selectors/URLs.
- Implement a safe Electron-main scraper service for product testing:
  - Offline sample-data mode must work without network access.
  - Optional URL mode may fetch a CSV/JSON document through the main process.
  - Scraped rows must be written to a CSV under Electron `app.getPath('userData')`.
  - Start, pause/resume where practical, cancel, and analyze actions must be exposed through a narrow context-isolated IPC API.
- Analysis must report row count, unique symbols, date range, average/min/max close, total volume, and top absolute close-to-open movers.
- The Scraper tab must show status, progress, output path, analysis cards, and a data preview.

## Update-notification contract
- Add an update banner in the renderer and an Electron-main update check.
- Version checks must compare the running app version to a packaged update manifest; an optional remote manifest URL may be supplied with `BAZZAR_UPDATE_MANIFEST_URL`.
- The manifest must support `enabled`, `latestVersion`, `message`, `url`, and `publishedAt`.
- Version 1.1.0 ships with the notification toggled on so installed 1.1.0 instances display the available-update banner.
- This is a notification mechanism, not a full auto-updater.

## Installer contract
- Build output: Windows NSIS installer (`Bazzar Terminal Setup <version>.exe`).
- Default install location: per-user Windows app directory managed by electron-builder.
- Create desktop and Start Menu shortcuts.
- Allow the user to choose the installation directory.
- Include the complete original repository payload and generated dependency manifests.
- No network access is required after installation for the desktop shell to launch.

## Verification contract
- `npm ci` must succeed.
- `npm run build` must produce `dist/`.
- `npm run dist:win:nsis` must produce a `.exe` NSIS installer under `release/` without requiring wine; `npm run dist:win` remains the standard electron-builder path for Windows/wine-capable builders.
- Packaging file lists must be inspected to confirm the repository payload is present.

---

# Bazzar Data Platform Specification (v1.2.0)

Binding contract for the OpenAlgo/DuckDB data layer, the local Python chart
renderer, and the renderer UI rework. All modules MUST implement to these
interfaces exactly.

## Architecture
- **DuckDB** is the only data store. `backend/db_config.json` is the single
  database setup configuration file: it defines every table, the full index
  universe, the macro indicator registry, and the fetch policy. The entire
  database is created from — and only from — this file.
- **Market data source:** OpenAlgo REST API with the Motilal Oswal broker
  (https://github.com/marketcalls/openalgo-docs/blob/main/connect-brokers/brokers/motilal-oswal.md).
  Per those docs: `BROKER_API_KEY` = Motilal client code, `BROKER_API_SECRET`
  = generated API key, plus the OpenAlgo host `OPENALGO_API_KEY` and
  `OPENALGO_BASE_URL` (default `http://127.0.0.1:5000`).
- **Credentials never enter git.** They live in `.env` (gitignored). Only
  `.env.example` with empty placeholders is committed.
- **Rate-limit policy:** daily timeframe (`interval: "D"`) only. No
  intraday/smaller timeframe is ever requested. Symbols are processed in
  strict alphabetical order; a `fetch_checkpoint` table records the last
  completed symbol so an interrupted pull resumes at the next symbol.
- **Charts:** TradingView / lightweight-charts is fully removed. Charts are
  built locally in Python with matplotlib (Agg backend), dark terminal theme,
  rendered to PNG and served over the local API.
- **Data dir:** `BAZZAR_DATA_DIR` (default `./data`, gitignored) holds
  `bazzar.duckdb` and the chart cache.

## Python package `backend/`
- `db_config.json` — config file (tables, indices universe incl. every index
  listed in the instructions, macro registry w/ source+url, fetch policy).
- `db.py` — `get_connection()`, `initialize_database(config_path)` creating
  tables: `securities`, `daily_ohlcv`, `index_daily`, `index_master`,
  `macro_series`, `macro_observations`, `benchmark_series`,
  `benchmark_observations`, `fetch_checkpoint`.
- `openalgo_client.py` — compatibility shim re-exporting from
  `providers/openalgo.py` (kept for existing imports).
- `providers/` — market-data provider abstraction (P3): `base.py`
  (`MarketDataProvider` protocol, `Bar`/`Instrument`/`Quote` types,
  `ProviderError`/`ProviderAuthRequired`/`ProviderCapabilityError`),
  `ratelimit.py` (shared token bucket), `kite.py` (Zerodha Kite Connect —
  primary), `openalgo.py` (fallback), `nse_bhavcopy.py` (free EOD fallback),
  `__init__.py` (registry + `get_provider()` factory + `load_token_map()`).
- `kite_auth.py` — Kite session store in the OS keyring ONLY (access token +
  API secret never touch .env/DB/git); CLI `set-secret|status|logout`.
- `sync_instruments.py` — Kite instrument master → `securities` upsert
  (instrument_token/lot_size/tick_size; index segment → `*_INDEX` exchanges;
  vanished listings deactivated, never deleted).
- `fetch_daily.py` — alphabetical daily OHLCV pull with checkpoint resume;
  `--provider` flag (P3), per-symbol failures → partial run.
- `fetch_indices.py` — daily OHLC + 52-week high/low for every index in
  `index_master`; same `--provider` semantics.
- `macro.py` — macro indicator registry loader + observation import helpers.
- `reconcile.py` — data-quality checks (P4-C): kite-vs-bhavcopy close
  reconciliation, macro/benchmark freshness vs configured cadence; results
  are appended to the `data_quality` table inside an `ingestion_run` audit
  context. CLI `python3 -m backend.reconcile` (exit 1 on fail-severity).
- `sources/` — government/open-data fetchers (P4): `rbi.py`, `intl.py`,
  `mospi.py`, `nse_open.py`, plus `sync_all.py` (one-command seed:
  all sources + reconcile; missing keys/offline = clean skips, exit 1 only
  on hard failures).
- `charts.py` — matplotlib candlestick/line PNG renderers + the cache-first
  chart store (`<data dir>/cache/charts/...` + `manifest.json`, keyed by data
  fingerprint) (P5).
- `middleware.py` — `RequestIDMiddleware` (X-Request-ID + structlog binding),
  `BearerAuthMiddleware` (P5 token gate), `WeakETagMiddleware` (304s on the
  slow-changing GETs), and the shared `error_envelope()` shape (P5).
- `schemas.py` — pydantic response models wired as `response_model=` on the
  main GET endpoints; this file *is* the machine-checked API contract (P5).
- `server.py` — FastAPI app (uvicorn, port `BAZZAR_API_PORT`, default 8787,
  loopback-only bind to `127.0.0.1`).

## Local HTTP API contract (base `http://127.0.0.1:8787`)

Versioning & envelope (P5, roadmap 5.1–5.3):
- All routes are mounted under `/api/v1`; the flat `/api` mount remains as a
  **deprecated** alias for one release (identical responses, excluded from
  the OpenAPI schema). The renderer calls `/api/v1` only.
- **Auth:** when `BAZZAR_API_TOKEN` is set (the Electron shell generates a
  random 32-byte hex token per launch and passes it to the sidecar), every
  `/api/*` request must carry `Authorization: Bearer <token>` — else 401.
  When the variable is unset (plain `python -m backend.server` dev run) the
  API is open: a documented development fallback. Sole exemption:
  `GET /api/auth/kite/callback` (the external-browser Kite redirect cannot
  know the token; its one-time `request_token` is the credential).
- **Error envelope:** every non-2xx JSON error is
  `{"error": {"code": "<snake_case>", "message": "<human readable>"}}` —
  HTTPException → snake_case of its status phrase, request validation →
  `422 validation_error`, anything unexpected → `500 internal_error`
  (traceback logged server-side with the request id, never leaked).
- Every response carries an `X-Request-ID` header (uuid4; an incoming
  `X-Request-ID` is echoed) bound to the server log lines.
- CORS allows exactly `http://localhost:5173`, `http://127.0.0.1:5173` and
  `"null"` (packaged Electron `file://` pages send `Origin: null`); methods
  GET/POST, headers Authorization/Content-Type/If-None-Match.
- Health trio: `GET /api/health` is **liveness** (always 200
  `{ok, db, version}` when the process serves); `GET /api/health/ready` is
  **readiness** (DuckDB opens + migrations at latest + data dir writable →
  200 `{status: "ready", db, version}`, else 503 envelope);
  `GET /api/health/data` is the data-quality report below.

Endpoints (paths shown under the deprecated alias; prepend `/v1` for the
canonical mount):
- `GET /api/health` → `{ok, db, version}` (liveness)
- `GET /api/health/ready` → `{status, db, version}` (readiness; 503 envelope
  when the data dir is unwritable, DuckDB fails, or migrations are pending)
- `GET /api/health/data` → `{status, checks, summary, asOf}` — data-quality
  status from `data_quality` (P4-C): latest row per (check_name, target);
  `red` on an unresolved fail younger than 48h, `amber` on any current warn
  or older unresolved fail, else `green`; empty table → green, never 500
- `GET /api/home/indices` → `[{name, symbol, value, change, changePct, asOf}]`
  (value = current/last close, change = pointwise change, changePct = %)
- `GET /api/indices` → `[{symbol, name, exchange, open, high, low, close,
  yearHigh, yearLow, asOf}]` for the full index universe
- `GET /api/indices/{symbol}/chart.png` → PNG candlestick chart (daily)
- `GET /api/stocks/{symbol}/chart.png?exchange=NSE` → PNG candlestick chart
- `GET /api/search?q=<text>&limit=10` → `[{symbol, name, exchange}]` using the
  dictionary method: case-insensitive prefix matches first, then substring,
  then token matches, ranked, over the `securities` dictionary
- `GET /api/quotes?symbols=A,B` → `{symbols: {A: {value, change, changePct, asOf}|null}}`
- `GET /api/benchmarks` → `{groups: [{key, title, unit, series: [{name,
  latest, change, asOf}]}]}` with keys `rbi_gsec`, `us_treasury_10y`, `sgb`,
  `repo_rates` (RBI repo vs US Fed funds)
- `GET /api/benchmarks/{key}/chart.png` → PNG line chart
- `GET /api/macro` → `[{key, title, category, unit, frequency, source,
  sourceUrl, latest, period, change}]` for the whole macro registry
- `GET /api/auth/kite/login-url` → `{url}` for the Zerodha redirect login
  (503 when `KITE_API_KEY` is not configured)
- `GET /api/auth/kite/callback?request_token=...` → exchanges the token for a
  session stored in the OS keyring → `{status: "connected", user_id, user_name}`
- `GET /api/auth/kite/status` → non-secret auth state `{configured,
  api_key_set, authenticated, user, login_time, expires_hint}` — never tokens
- `POST /api/auth/kite/disconnect` → clears the session (keeps the API secret)
- All list endpoints return `null`/`[]` fields (never fabricated numbers)
  when data has not been synced yet; the UI shows an "awaiting data sync"
  state.

## Renderer contract (`src/`)
- API base: `import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8787'`,
  centralised in `src/api.js` (tiny fetch wrapper + `chartUrl()` helpers).
- Auth (P5): the renderer obtains the per-launch bearer token from
  `window.bazzar.getApiToken()` (Electron preload → main-process IPC) and
  `src/api.js` sends it as `Authorization: Bearer <token>` on every request.
  Chart PNGs cannot carry headers in an `<img>` tag, so `ChartImage.jsx`
  fetches them as authenticated blobs (`fetchChartObjectUrl`) and renders
  object URLs (revoked on cleanup); CSP `img-src` therefore includes
  `blob:`. All paths are the versioned `/api/v1/...`.
- `src/components/SearchInput.jsx` — reusable dictionary-search input with
  debounced `/api/search` dropdown + keyboard navigation; used at every stock
  search location (Home portfolio add, Equity watchlist add, deep-dive
  pickers).
- `Home.jsx` — index cards show value + pointwise change + % from
  `/api/home/indices`; portfolio stock input uses `SearchInput`; no Math.random.
- `Benchmarks.jsx` (new tab) — the four moved benchmark groups (RBI G-Sec,
  US Treasury 10Y, SGB, RBI vs US Fed repo) as chart cards (PNG from backend)
  plus the macro indicator section grouped by category from `/api/macro`.
- `Indices.jsx` (new tab) — searchable/sortable table of the full index
  universe with O/H/L/C + year low/high; selecting a row shows its backend
  PNG chart.
- `MarketAnalysis.jsx` — benchmark charts removed (moved to Benchmarks); keeps
  USDINR (backend series), IndexContribution, AppInfoCard; mock data removed.
- `Commodities.jsx` / `Currency.jsx` — no Math.random placeholders; values
  come from `/api/quotes`, showing "—" when unsynced.
- Deleted: `src/mockData.js`, `ChartDashboard.jsx`, `RBIBondsChart.jsx`,
  `RepoRatesChart.jsx`, `SGBChart.jsx`, `USTreasuryBondsChart.jsx`,
  `USDINRChart.jsx` (replaced by backend-PNG chart cards); the
  `lightweight-charts` dependency is removed from `package.json`.
- `src/components/KiteStatus.jsx` — topbar pill polling
  `/api/auth/kite/status` every 30s; "Connect Kite" opens the login URL in
  the system browser via the allowlisted `shell:open-external` IPC.
- UI/UX: keep the existing black/gold theme (`src/theme.js`).

## Electron / config glue (main agent)
- `electron/main.cjs` optionally spawns the Python backend sidecar
  (`python -m backend.server`, guarded, tolerant of missing Python).
- `index.html` CSP gains `connect-src 'self' http://127.0.0.1:8787` and
  `img-src 'self' data: http://127.0.0.1:8787`.
- `.env.example`, `.gitignore` (`data/`, `.env`, chart cache), README update.

## Verification
- `python3 -m backend.db` bootstrap smoke test creates the DB from config.
- `python3 -c "from backend.server import app"` import test passes.
- `npm ci && npm run build` succeeds with no lightweight-charts references.
