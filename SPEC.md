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
- `openalgo_client.py` — `OpenAlgoClient` reading `.env`; methods
  `history(symbol, exchange, start_date, end_date)` (interval hardcoded "D"),
  `quotes(symbol, exchange)`, `search(query)`; polite rate limiting.
- `fetch_daily.py` — alphabetical daily OHLCV pull with checkpoint resume.
- `fetch_indices.py` — daily OHLC + 52-week high/low for every index in
  `index_master`.
- `macro.py` — macro indicator registry loader + observation import helpers.
- `charts.py` — matplotlib candlestick/line PNG renderers.
- `server.py` — FastAPI app (uvicorn, port `BAZZAR_API_PORT`, default 8787).

## Local HTTP API contract (base `http://127.0.0.1:8787`)
- `GET /api/health` → `{ok, db, version}`
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
- All list endpoints return `null`/`[]` fields (never fabricated numbers)
  when data has not been synced yet; the UI shows an "awaiting data sync"
  state.

## Renderer contract (`src/`)
- API base: `import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8787'`,
  centralised in `src/api.js` (tiny fetch wrapper + `chartUrl()` helpers).
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
