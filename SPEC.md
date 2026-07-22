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
