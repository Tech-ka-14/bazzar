-- 0002_ops_tables.sql — P2 operational tables: write validation quarantine,
-- ingestion audit trail, and the exchange trading calendar.
-- These tables are owned by migrations (not db_config.json) because they use
-- sequences/defaults the config DDL generator does not express.

-- Quarantine for rows that fail write validation (never silently dropped).
CREATE SEQUENCE IF NOT EXISTS data_rejects_id_seq START 1;

CREATE TABLE IF NOT EXISTS data_rejects (
    id BIGINT PRIMARY KEY DEFAULT nextval('data_rejects_id_seq'),
    job VARCHAR NOT NULL,
    table_name VARCHAR NOT NULL,
    payload VARCHAR NOT NULL,
    reason VARCHAR NOT NULL,
    rejected_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Audit trail for every ingestion job run (drives asOf / staleness reporting).
CREATE SEQUENCE IF NOT EXISTS ingestion_runs_id_seq START 1;

CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id BIGINT PRIMARY KEY DEFAULT nextval('ingestion_runs_id_seq'),
    job VARCHAR NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    rows_written BIGINT NOT NULL DEFAULT 0,
    rows_rejected BIGINT NOT NULL DEFAULT 0,
    status VARCHAR NOT NULL,
    error VARCHAR
);

-- Exchange trading calendar. Rows exist only inside the seeded coverage
-- window (see backend/data/nse_calendar.csv); outside coverage a date's
-- status is UNKNOWN and validators must not reject on calendar grounds.
CREATE TABLE IF NOT EXISTS trading_calendar (
    exchange VARCHAR NOT NULL,
    date DATE NOT NULL,
    is_trading_day BOOLEAN NOT NULL,
    holiday_name VARCHAR,
    PRIMARY KEY (exchange, date)
);
