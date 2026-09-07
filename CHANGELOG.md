# Changelog

All notable changes to Bazzar Terminal. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
versioning: [SemVer](https://semver.org/).

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
