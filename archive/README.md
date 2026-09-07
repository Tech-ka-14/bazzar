# Archive

Legacy sources kept for audit/reference only. **Nothing here is imported,
executed, or packaged into the running application.**

- `frontend-legacy/` — the original root-level React components (`.jsx`) that
  were repaired and moved to `src/components/` in v1.1, plus
  `ChartDashboard.py`, an early 85-line draft of what became
  `quant/portfolio/fundamental_analyzer.py`.
- `go-scraper/` — the Go/Fyne + Colly scraper prototype. Its `main.go` still
  points at a placeholder URL and it is not wired to the Electron app; the
  Electron main process provides the supported scraper test-bench instead.

If a module here is revived, move it into `quant/` (or `src/`) and bring it
under lint/format/test gates first.
