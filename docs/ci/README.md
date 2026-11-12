# Staged CI configuration (P6, roadmap 6.1/6.2)

The files in this directory are **staged, not active**. The release
automation cannot push files under `.github/`, so CI additions live here
until a maintainer copies them into place (a one-time, one-minute step):

```bash
cp docs/ci/security.yml .github/workflows/security.yml
cp docs/ci/dependabot.yml .github/dependabot.yml
git add .github && git commit -m "ci: activate security gate + dependabot (P6)"
```

## What each file does

- **`security.yml`** — three jobs on every push/PR plus a weekly sweep:
  1. **gitleaks** (full-history secret scan using `.gitleaks.toml`),
  2. **pip-audit** on the fully resolved Python environment,
  3. **npm audit --audit-level=high**.
  Locally the same gates are `make secrets` and `make audit`. Known accepted
  exceptions are listed in `SECURITY.md` ("Dependency audit exceptions") —
  when the audit jobs start failing, either bump the dependency or extend
  that list with a justification.

- **`dependabot.yml`** — weekly Dependabot PRs for the `pip`, `npm`, and
  `github-actions` ecosystems. Major upgrades of `electron`,
  `electron-builder`, `vite`, and `vitest` are ignored on purpose: they are
  breaking and are handled manually (see `SECURITY.md`).
