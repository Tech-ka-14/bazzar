-- 0004_data_quality.sql — P4-C (roadmap 4.5): append-only data-quality audit.
-- backend/reconcile.py writes one row per check result (never updated, never
-- deleted); /api/health/data reads the latest row per (check_name, target).
-- Owned by migrations (not db_config.json) because it uses a
-- sequence/default the config DDL generator does not express — same pattern
-- as the 0002 ops tables.

CREATE SEQUENCE IF NOT EXISTS data_quality_id_seq START 1;

CREATE TABLE IF NOT EXISTS data_quality (
    id BIGINT PRIMARY KEY DEFAULT nextval('data_quality_id_seq'),
    check_name VARCHAR NOT NULL,
    target VARCHAR NOT NULL,
    period VARCHAR,
    severity VARCHAR NOT NULL,
    message VARCHAR NOT NULL,
    details VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
