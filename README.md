# Bazzar Terminal

Windows desktop installer for the Bazzar financial-terminal UI, built with
Electron + Vite + React + Tailwind CSS.

The installer ships two things:

1. **Bazzar Terminal** — an Electron desktop app (`dist/` renderer +
   `electron/` shell) with a login screen, navigation (Home, Equity,
   Commodities, Currency, Market Analysis, International Markets, Scraper),
   interactive charts (`lightweight-charts`), a scraper test-bench, and an
   update-notification banner.
2. **Repository payload** — the complete original repository source
   (180 Python quant modules, Go/Fyne scraper prototypes, JSX sources,
   `SPEC.md`, `requirements.txt`, `go.mod`) installed under
   `resources/repository/` for audit/development use. The Python and Go
   sources are shipped as source only; nothing is executed or packaged as
   binaries.

## Prerequisites

- Node.js 20+ and npm
- Windows (or a machine with wine/makensis) for producing the NSIS installer

## Install dependencies

```bash
npm install   # or: npm ci
```

## Develop

```bash
npm run dev                                  # Vite dev server (browser mode)
# in another terminal, with the dev server running:
VITE_DEV_SERVER_URL=http://localhost:5173 npm start
```

## Build the renderer

```bash
npm run build     # outputs dist/
```

## Build the Windows installer

Recommended wine-free path (works on Windows with NSIS installed and on Linux
with the makensis binary cached by electron-builder):

```bash
npm run dist:win:nsis
```

This first builds `release/win-unpacked/` with electron-builder and then
compiles `installer/BazzarTerminal.nsi` into
`release/Bazzar Terminal Setup <version>.exe` (NSIS, x64).

Alternatively, on Windows or a Linux machine with wine installed, the standard
electron-builder NSIS pipeline also works:

```bash
npm run dist:win
```

Installer behavior:

- Per-user install under the default Windows per-user app directory
- User can choose the installation directory (`oneClick: false`,
  `allowToChangeInstallationDirectory: true`)
- Creates desktop and Start Menu shortcuts ("Bazzar Terminal")
- Installs the repository payload to `resources/repository/`
- No network access is required after installation to launch the shell

## Security model

- `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`
- Renderer talks to the main process only through the narrow, context-isolated
  `window.bazzar` preload API:
  - `getAppInfo()` — app/version/repository-payload information
  - `scraperStart/Pause/Resume/Cancel/GetStatus/Analyze` + `onScraperStatus`
    — scraper test-bench control and status pushes
  - `checkForUpdates()` — update-notification check
- A Content-Security-Policy is set in `index.html`; new windows and external
  navigation are denied in the main process.

## Scraper test-bench

The **Scraper** tab is a safe test-bench for product testing. All scraping,
parsing, CSV writing, and analysis run in the Electron **main process**
(`electron/main.cjs`); the renderer only calls the narrow IPC API listed
above. The original Go/Fyne scraper in the repository payload remains
source-only and is **not** a runtime dependency (its `main.go` still points at
a placeholder URL).

Modes:

- **Offline sample data (required, no network):** generates a deterministic
  OHLCV dataset (8 symbols × 60 trading days) and writes it, in chunks, to
  `daily_ohlcv.csv` under Electron `app.getPath('userData')`.
- **Fetch CSV/JSON URL (optional):** downloads a CSV or JSON document through
  the main process (`http`/`https`, redirects + size/timeout limits), parses
  it, and writes the normalized rows to the same output file.

Column normalization accepts `Ticker`/`Symbol`, `Open`, `High`, `Low`,
`Close`, `Volume`, and an optional `Date` (case-insensitive, with a few common
aliases). Malformed rows are skipped and counted; empty or unparseable input
returns a structured error instead of crashing.

Controls: **Start**, **Pause**, **Resume**, **Cancel**, **Analyze CSV**. The
tab shows live status/progress (pushed over `scraper:status` events), the
output path, analysis cards (row count, unique symbols, date range,
average/min/max close, total volume, top absolute close-to-open movers), and a
25-row data preview.

## Update notifications

This is a notification mechanism, **not** a full auto-updater.

- The packaged manifest `electron/update-manifest.json` ships inside the app
  (`electron/**` is part of the electron-builder file set) with fields
  `enabled`, `latestVersion`, `message`, `url` (GitHub releases page), and
  `publishedAt`.
- `window.bazzar.checkForUpdates()` (IPC `update:check`) compares the running
  app version (`app.getVersion()`) against the manifest's `latestVersion`.
  When `enabled` is true and `latestVersion` is at least the running version,
  the renderer shows a dismissible banner with the message and releases URL.
- Version 1.1.0 ships with the notification toggled **on**
  (`latestVersion: 1.1.0`, `enabled: true`), so installed 1.1.0 instances
  display the banner immediately. To notify about a future release, bump
  `latestVersion` to a version newer than the installed app.
- An optional remote manifest URL can be supplied via the
  `BAZZAR_UPDATE_MANIFEST_URL` environment variable; if the remote fetch
  fails, the packaged manifest is used as a fallback.

## Project layout

```
electron/main.cjs      Electron main process (secure defaults + IPC + scraper/update services)
electron/preload.cjs   Context-isolated preload (window.bazzar)
electron/update-manifest.json  Packaged update-notification manifest
installer/icon.base64    Text-encoded app icon (decoded to build/icon.ico)
scripts/prepare-icon.cjs Decodes the app icon before packaging
scripts/prepare-payload.cjs  Stages the repository payload into build/repository
src/                   Repaired React app (theme, components, mock data)
build/repository/      Staged repository payload (generated, git-ignored)
dist/                  Vite production build output
release/               electron-builder installer output
*.jsx (repo root)      Original component sources, kept untouched
*.py / *.go            Original Python/Go sources, kept untouched
requirements.txt       Python third-party dependencies
go.mod                 Go scraper dependency manifest (source-only)
SPEC.md                Product/installer specification
```
