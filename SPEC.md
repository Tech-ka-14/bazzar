# Bazzar Terminal — Product & Installer Specification (v1.1.0)

This document is the single source of truth for the Bazzar Terminal desktop
app and the Windows installer. It merges the repository specification with
the packaging specification agreed with the user. For the overall system
architecture and hard engineering rules, see ARCHITECTURE.md.

## 1. Product overview

- **Name:** Bazzar Terminal
- **Platform:** Windows desktop (Electron shell around the Bazzar UI)
- **Stack:** Electron + Vite + React + Tailwind CSS
- **UI source of truth:** `src/` React app (navigation: Home, Equity,
  Commodities, Currency, Market Analysis, International Markets, Scraper)
  with interactive charts (`lightweight-charts`), a scraper test-bench, and
  an update-notification banner
- **Repository payload:** the full original repository source — 180 Python
  quant modules (now organized under `quant/`), Go/Fyne scraper prototypes
  (`archive/go-scraper/`), legacy JSX drafts (`archive/frontend-legacy/`),
  `SPEC.md`, `requirements.txt`, `go.mod` — shipped as *source only* inside
  the installer for audit/development use

## 2. Installer deliverable

- **Format:** NSIS installer (`Bazzar Terminal Setup <version>.exe`, x64)
- **Install scope:** per-user install under the default Windows per-user app
  directory; the user can change the installation directory
  (`oneClick: false`, `allowToChangeInstallationDirectory: true`)
- **Shortcuts:** desktop + Start Menu ("Bazzar Terminal")
- **Payload:**
  1. the Electron app (renderer `dist/` + `electron/` shell), and
  2. the repository payload installed to `resources/repository/`
- **Offline:** no network access required after installation to launch the
  shell

## 3. Build pipeline

- Renderer build: `npm run build` (Vite, outputs `dist/`)
- Packaging: `npm run dist:win:nsis`
  1. `npm run build` — Vite production build
  2. `npm run prepare:icon` — decodes `installer/icon.base64` to
     `build/icon.ico`
  3. `npm run prepare:payload` — stages the repository payload into
     `build/repository/` (via electron-builder `extraResources` →
     `resources/repository/`)
  4. `electron-builder --win --x64 --dir` — produces
     `release/win-unpacked/`
  5. `scripts/build-nsis.cjs` — compiles `installer/BazzarTerminal.nsi`
     with makensis into `release/Bazzar Terminal Setup <version>.exe`
- Alternative: `npm run dist:win` (electron-builder's own NSIS pipeline;
  needs wine on Linux)

## 4. Security model

- `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`
- Renderer reaches the main process only through the context-isolated
  `window.bazzar` preload API:
  - `getAppInfo()` — app/version/repository-payload information
  - `scraperStart/Pause/Resume/Cancel/GetStatus/Analyze` + `onScraperStatus`
    — scraper test-bench control and status pushes
  - `checkForUpdates()` — update-notification check
  - `openExternal(url)` — allowlisted https URLs only (Kite login, P3)
- A Content-Security-Policy is set in `index.html`; new windows and external
  navigation are denied in the main process
- **P6 (security pass):** all renderer permission requests are denied and
  logged; every IPC payload is validated against a zod schema
  (`electron/validation.cjs`). See the "Security rules (P6)" section below
  and SECURITY.md for the full model.

## 5. Scraper test-bench

- Safe test-bench for product testing; all scraping/parsing/CSV/analysis
  runs in the Electron **main process** (the renderer has no Node access)
- Modes:
  - **Offline sample data (required, no network):** deterministic OHLCV
    dataset (8 symbols × 60 trading days) written in chunks to
    `daily_ohlcv.csv` under Electron `app.getPath('userData')`
  - **Fetch CSV/JSON URL (optional):** downloads through the main process
    with redirects + size/timeout limits, normalizes, and writes the same
    output file
- Column normalization: `Ticker`/`Symbol`, `Open`, `High`, `Low`, `Close`,
  `Volume`, optional `Date` (case-insensitive + common aliases); malformed
  rows are skipped and counted
- The original Go/Fyne scraper in the repository payload remains
  source-only and is **not** a runtime dependency

## 6. Update notifications

- Notification mechanism only — **not** a full auto-updater
- Packaged manifest `electron/update-manifest.json` (shipped inside the app)
  with `enabled`, `latestVersion`, `message`, `url`, `publishedAt`
- The banner shows when `enabled` is true and `latestVersion` is at least
  the running app version (so 1.1.0 with `latestVersion: 1.1.0` displays
  immediately — "notification toggled on")
- Optional remote manifest via `BAZZAR_UPDATE_MANIFEST_URL`; packaged
  manifest is the fallback on any fetch failure

## 7. Versioning & repository hygiene (P0/P1)

- Single repository; quant modules live in the `quant/` package
  (`risk`, `copulas`, `timeseries`, `portfolio`, `stats`, `pricing`)
- Legacy JSX drafts in `archive/frontend-legacy/`; Go scraper prototype in
  `archive/go-scraper/` (reference only)
- `pyproject.toml` (ruff, mypy, pytest config), `requirements.txt` +
  `requirements-dev.txt`, pre-commit hooks (ruff, ruff-format, gitleaks),
  Makefile (`make setup` / `make check` / `make dev`)
- GitHub Actions CI (`.github/workflows/ci.yml`): Python gate (ruff, mypy,
  pytest) + Node gate (eslint, prettier, vitest, vite build) + gitleaks
  scan; Dependabot for pip/npm/github-actions
- Release history tracked in CHANGELOG.md (Keep a Changelog + SemVer)

---

# Bazzar Data Platform — Product & Engineering Specification (v1.2.0)

Goal: Replace every dummy/placeholder dataset in the Bazzar Terminal with a
local, auditable Python data layer (DuckDB + FastAPI + matplotlib) that
serves real daily market data to the existing Electron/React UI. Daily
timeframe only — rate limits first.

## Context

- The UI (Home, Equity, Commodities, Currency, Market Analysis,
  International Markets, Scraper) currently renders dummy data.
- The working title list: NIFTY 50, NIFTY Bank, NIFTY IT, India VIX,
  BSE Sensex, NIFTY Midcap, USD/INR, Gold, Silver, Crude Oil, plus the
  complete NSE/BSE/MCX index universe.
- Benchmarks/macro tab content is defined in `backend/db_config.json`
  (G-Sec 10Y/5Y, US 10Y, SGB, RBI repo/reverse-repo, FII/DII flows, CPI,
  WPI, IIP, GDP, forex reserves, US Fed funds).
- Zerodha Kite Connect (P3) is the primary market-data provider
  (respecting the 3 req/s historical API limit), with OpenAlgo + NSE
  bhavcopy as fallbacks.

## Targets

- Local DuckDB database created from a single config file
  (`backend/db_config.json`): schema (tables), the full NSE/BSE/MCX index
  universe, macro-indicator registry, fetch policy. The entire DB is
  created from config — no hidden schema in code.
- Local FastAPI server (`python3 -m backend.server`, default
  http://127.0.0.1:8787, loopback only) serving JSON + matplotlib PNG
  charts to the Electron UI; the Electron shell spawns it as a sidecar.
- Daily timeframe only. Strict alphabetical symbol order. Resumable pulls
  via a `fetch_checkpoint` table.
- Every fetch job audited in `ingestion_runs`; rejected rows quarantined in
  `data_rejects` with a reason.
- Secrets: KITE_API_SECRET and the daily access token live in the OS
  keyring ONLY (`python3 -m backend.kite_auth set-secret`); .env holds only
  the non-secret KITE_API_KEY. Never in DB, never in git.

## Verification
- `python3 -m backend.db` bootstrap smoke test creates the DB from config.
- `python3 -c "from backend.server import app"` import test passes.
- `npm ci && npm run build` succeeds with no lightweight-charts references.

---

# Security rules (P6, roadmap 6.1–6.5)

Binding rules; `SECURITY.md` holds the full threat model and secrets
inventory and is the authoritative pointer for this section.

- **DB safety (6.4):** every DuckDB `.execute()`/`.executemany()` call uses a
  static SQL string with bind parameters. String-interpolated SQL is
  forbidden; the only escape hatch is `backend.backup._sql_string_literal()`
  for the two statements that cannot take bind parameters (`EXPORT/IMPORT
  DATABASE`). Enforced by the AST gate `tests/test_sql_safety.py`. Any
  filesystem path derived from user input (symbol, key, kind) must pass
  through `backend.charts._sanitize_name()` before being joined into a path;
  traversal rejection is tested in `tests/test_path_traversal.py`.
- **IPC validation (6.3):** every `ipcMain.handle` payload is untrusted
  renderer input and must be validated against a zod schema in
  `electron/validation.cjs` before use. The renderer gets no new
  `shell.openExternal` hosts without a code review of the allowlist.
  Permission requests are denied by default
  (`setPermissionRequestHandler`/`setPermissionCheckHandler`); new windows
  and off-origin navigation stay denied.
- **Secrets (6.1):** the secrets inventory in `SECURITY.md` is exhaustive:
  `KITE_API_SECRET` and the Kite access token live in the OS keyring ONLY;
  `.env.example` documents non-secret values with empty placeholders only;
  `.env` stays gitignored. Any new secret added to the codebase must update
  the inventory table first. The tree must stay clean under gitleaks
  (`.gitleaks.toml`) and the detect-secrets baseline (`.secrets.baseline`).
- **Dependency security (6.2):** `make audit` (pip-audit + npm audit
  `--audit-level=high`) runs before every release. Accepted exceptions are
  listed, with justification and review date, in `SECURITY.md` → "Dependency
  audit exceptions"; anything not listed there must be fixed or the release
  is blocked.
