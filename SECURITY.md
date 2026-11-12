# Security — Bazzar Terminal

Scope: the Bazzar Terminal desktop app (Electron shell + React renderer +
local FastAPI/DuckDB sidecar). This document is the single pointer for the
threat model, the secrets inventory, the audit process, and the hardening
checklist (P6, roadmap 6.5).

## Reporting

This is a personal, single-user desktop application. If you find a security
issue, open a private GitHub security advisory on the repository rather than
a public issue.

## Threat model

Bazzar Terminal is a **local, single-user desktop app**. The FastAPI sidecar
binds `127.0.0.1` only and is never reachable off-machine. There is no
multi-user surface, no server deployment, and no telemetry.

The realistic threats, in rough priority order:

1. **Malicious renderer content** (XSS in the React UI, or a compromised
   npm dependency shipping hostile renderer code). Mitigations:
   `contextIsolation`, `sandbox`, no `nodeIntegration`, a strict CSP in
   `index.html`, a narrow preload API, schema-validated IPC payloads
   (`electron/validation.cjs`, zod), deny-all permission handlers, denied
   window-open and off-origin navigation, and an https-only host allowlist
   for `shell.openExternal` (Kite domains only).
2. **Token theft by another local process.** The sidecar bearer token
   (below) means any process that can read the Electron renderer's memory or
   the IPC channel could call the local API. Impact is limited to reading
   market data and the non-secret Kite auth status; no secrets are ever
   served over the API (the keyring never leaves the OS).
3. **Dependency CVEs** (npm + pip). Mitigated by the audit process below;
   residual accepted risks are listed in "Dependency audit exceptions".
4. **Data-at-rest on a shared machine.** The DuckDB database and chart cache
   under `BAZZAR_DATA_DIR` are world-readable if your OS account is not.
   Market data is not sensitive to us, but your portfolio symbols and Kite
   user id may be. See "Data at rest".
5. **Credential phishing at the Kite login.** Login happens in the *system
   browser* on `kite.trade` (opened via the allowlisted `openExternal`),
   never inside the app window — the app never sees your Zerodha password or
   TOTP. Verify the browser address bar shows `kite.trade` before logging in.

## Local API token lifecycle

- Generated **per launch** by the Electron main process:
  `crypto.randomBytes(32).toString('hex')` (`electron/main.cjs`).
- Passed to the sidecar as the `BAZZAR_API_TOKEN` environment variable only —
  never written to disk, never logged, never persisted.
- Handed to the renderer over the `get-api-token` IPC and held **in memory
  only**; `src/api.js` attaches it as `Authorization: Bearer <token>` on
  every request. Chart PNGs are fetched as authenticated blobs
  (`ChartImage.jsx`) because `<img>` cannot carry headers.
- `BearerAuthMiddleware` (`backend/middleware.py`) rejects any `/api/*`
  request without the token with a 401 error envelope.
- **Sole exemption:** `GET /api/auth/kite/callback` (+ `/api/v1` twin).
  Justification: the external system browser is redirected there by
  kite.trade after the Zerodha login and cannot know the per-launch token;
  the one-time `request_token` issued by Kite is itself the credential, and
  the endpoint exchanges it immediately. No other path is exempt.
- When `BAZZAR_API_TOKEN` is unset (plain `python -m backend.server` dev run)
  the API is open — a documented development fallback; the packaged app
  always sets it.

## Secrets inventory

| Secret | Where it lives | Never in |
| --- | --- | --- |
| `KITE_API_SECRET` | OS keyring (`bazzar-terminal` service, key `kite_api_secret`) | .env, DB, git, logs |
| Kite daily `access_token` | OS keyring (key `kite_access_token`) | .env, DB, git, logs |
| Kite session meta (user id/name) | OS keyring (key `kite_session_meta`, non-secret JSON) | git |
| Sidecar bearer token | Process memory only (per launch) | disk, keyring, git |
| `KITE_API_KEY` | `.env` (gitignored) — **non-secret** client identifier | git |
| OpenAlgo / broker keys, `FRED_API_KEY`, `OGD_API_KEY` | `.env` (gitignored) | git |

Manage the Kite credentials with the CLI (prompts, never echoes):

```bash
python -m backend.kite_auth set-secret   # store KITE_API_SECRET in the keyring
python -m backend.kite_auth status       # non-secret auth state
python -m backend.kite_auth logout       # clear the session (keeps the secret)
```

`.env.example` documents only non-secret values with empty placeholders;
anything real goes into your local `.env` (gitignored) or the keyring.

## Dependency audit process

- **Locally:** `make audit` runs `pip-audit` (resolved environment) and
  `npm audit --audit-level=high`. `make secrets` runs gitleaks (or the
  detect-secrets baseline fallback).
- **Pre-commit:** `.pre-commit-config.yaml` runs gitleaks on staged changes
  (config `.gitleaks.toml`); `detect-secrets` with `.secrets.baseline` is the
  pip-installable fallback.
- **CI:** `docs/ci/security.yml` (gitleaks + pip-audit + npm audit, weekly
  sweep included) and `docs/ci/dependabot.yml` are staged — copy them into
  `.github/` to activate (see `docs/ci/README.md`).
- **Triage rule:** fix what is fixable with a compatible version bump;
  anything requiring a breaking major upgrade is assessed here instead of
  being force-upgraded blindly.

### Dependency audit exceptions (accepted, with justification)

Last reviewed: 2026-10-12 (v1.8.0).

| Package | Advisory | Disposition |
| --- | --- | --- |
| `autobahn` 19.11.2 (transitive via `kiteconnect`) | PYSEC-2020-25, PYSEC-2026-4027 (WebSocket payload DoS) | **Accepted.** `kiteconnect` hard-pins `autobahn[twisted]==19.11.2`; it cannot be bumped without forking the Kite client. The vulnerable code path is the WebSocket *ticker* (streaming); Bazzar uses REST only (daily OHLCV, per the SPEC rate-limit policy) and never runs the ticker, so the DoS surface is unreachable. |
| `electron` 33 (devDependency) | high via `extract-zip` | **Accepted.** Affects the *install-time* binary downloader (`@electron/get`), not the shipped app. Electron 34+ upgrades are planned but are breaking shell upgrades, not security emergencies. |
| `electron-builder` 25 (devDependency) | high/critical via `tar`, `cacache`, `node-gyp` | **Accepted.** Build-time-only tooling; never ships in the installed app. Fix requires the electron-builder 26 major upgrade — scheduled separately. |
| `vite` 5 / `vitest` 2 (devDependencies) | high/moderate dev-server and pool issues | **Accepted.** Dev/test-only tooling; the vulnerable paths are the Vite dev server and the vitest worker pool, neither of which ships. Fixes require the vite 8 / vitest 4 majors — scheduled separately. |

Re-run `make audit` after any dependency change; update this table whenever
the audit output changes.

## Data at rest

The DuckDB database, chart cache, and logs under `BAZZAR_DATA_DIR` (default
`./data`, gitignored) are protected only by OS file permissions. On a shared
Windows machine, enable **BitLocker** (whole disk) or **EFS** on the data
directory so other local users cannot read it. The OS keyring (Windows
Credential Manager) already protects the Kite secret and access token per
user account.

## Hardening checklist (OWASP-style, desktop)

- [x] Renderer sandboxed: `contextIsolation: true`, `sandbox: true`,
      `nodeIntegration: false`, `webSecurity: true`,
      `allowRunningInsecureContent: false`
- [x] Content-Security-Policy in `index.html` (self + local API + blob:
      images for authenticated chart blobs)
- [x] Narrow preload API only (`window.bazzar`); no generic IPC bridge
- [x] Every `ipcMain.handle` payload schema-validated (zod,
      `electron/validation.cjs`)
- [x] `shell.openExternal` restricted to https + exact host allowlist
      (Kite domains)
- [x] All permission requests denied and logged
      (`setPermissionRequestHandler` / `setPermissionCheckHandler`)
- [x] New windows denied (`setWindowOpenHandler`); off-origin navigation
      denied (`will-navigate`)
- [x] Sidecar binds `127.0.0.1` only; per-launch bearer token; CORS locked
      to dev origins + `"null"`
- [x] Single error envelope; no stack traces or internals leaked to clients
- [x] SQL: parameterized queries mandatory; f-string SQL blocked by an
      AST-based pytest gate (`tests/test_sql_safety.py`); the two DuckDB
      statements that cannot take bind parameters escape through
      `_sql_string_literal()`
- [x] User-derived filesystem paths sanitized (allowlist) before joining
      (`backend/charts.py::_sanitize_name`); traversal tests in
      `tests/test_path_traversal.py`
- [x] Secrets in OS keyring only; `.env` gitignored; gitleaks +
      detect-secrets scans clean
- [x] Dependency audits wired (`make audit`, staged CI, Dependabot config);
      exceptions documented above
- [x] Sidecar shut down on quit (SIGTERM, SIGKILL after grace)
- [ ] BitLocker/EFS on `BAZZAR_DATA_DIR` — user action on shared machines
- [ ] Copy `docs/ci/*` into `.github/` — maintainer action (403 boundary)
