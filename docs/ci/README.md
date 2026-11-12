# Staged CI configuration (P6, roadmap 6.1/6.2)

The files in this directory are **staged, not active**. The release
automation cannot push files under `.github/`, so CI additions live here
until a maintainer copies them into place (a one-time, one-minute step):

```bash
cp docs/ci/security.yml .github/workflows/security.yml
cp docs/ci/dependabot.yml .github/dependabot.yml   # optional, see below
git add .github && git commit -m "ci: activate security gate + dependabot (P6)"
```

**What already exists:** `.github/workflows/ci.yml` already runs a gitleaks
secret-scan job (it now picks up the root `.gitleaks.toml` automatically),
and a basic `.github/dependabot.yml` already watches pip/npm/github-actions.
The staged `security.yml` therefore only *adds* the two dependency-audit
jobs (pip-audit, npm audit) plus a weekly schedule — the gitleaks job in it
is a belt-and-braces duplicate you may delete when copying. The staged
`dependabot.yml` is an optional upgrade of the existing one (adds update
grouping and ignores breaking major upgrades of electron/electron-builder/
vite/vitest); skip the copy if you prefer the current config.

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
