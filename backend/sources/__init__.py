"""Government / open-data source fetchers (P4, roadmap steps 4.1–4.4).

Each source module pairs a pure parser (offline-testable against recorded
fixtures under tests/fixtures/) with a small HTTP client class (injectable
session, TokenBucket rate limit, tenacity backoff) and a ``sync()`` entry
point that writes through the validated upsert helpers inside an
``ingestion_run`` audit context.

Series codes / endpoint parameters live in db_config.json -> sources —
never hardcoded here (SPEC: db_config.json is the single source of truth).

Modules: ``rbi`` (RBI DBIE), ``intl`` (US Treasury + FRED), ``mospi``
(data.gov.in OGD), ``nse_open`` (holidays + FII/DII), and ``sync_all`` —
the one-command seed CLI that runs every source and then the
``backend.reconcile`` data-quality checks (P4-C).
"""
