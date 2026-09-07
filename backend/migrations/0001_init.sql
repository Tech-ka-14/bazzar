-- 0001_init.sql — baseline schema for the Bazzar Terminal data layer.
-- GENERATED from backend/db_config.json (the single source of truth for
-- domain tables). When db_config.json tables change, add a NEW migration
-- (NNNN_description.sql); never edit applied migrations.

CREATE TABLE IF NOT EXISTS securities (symbol VARCHAR, name VARCHAR, exchange VARCHAR, instrument_type VARCHAR, isin VARCHAR, active BOOLEAN, PRIMARY KEY (symbol, exchange));

CREATE TABLE IF NOT EXISTS daily_ohlcv (symbol VARCHAR, exchange VARCHAR, date DATE, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume BIGINT, PRIMARY KEY (symbol, exchange, date));

CREATE TABLE IF NOT EXISTS index_master (symbol VARCHAR, name VARCHAR, exchange VARCHAR, category VARCHAR, active BOOLEAN, sort_order INTEGER, PRIMARY KEY (symbol));

CREATE TABLE IF NOT EXISTS index_daily (symbol VARCHAR, date DATE, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, PRIMARY KEY (symbol, date));

CREATE TABLE IF NOT EXISTS macro_series (key VARCHAR, title VARCHAR, category VARCHAR, unit VARCHAR, frequency VARCHAR, source VARCHAR, source_url VARCHAR, PRIMARY KEY (key));

CREATE TABLE IF NOT EXISTS macro_observations (series_key VARCHAR, period VARCHAR, value DOUBLE, PRIMARY KEY (series_key, period));

CREATE TABLE IF NOT EXISTS benchmark_series (key VARCHAR, name VARCHAR, unit VARCHAR, PRIMARY KEY (key));

CREATE TABLE IF NOT EXISTS benchmark_observations (series_key VARCHAR, date DATE, value DOUBLE, PRIMARY KEY (series_key, date));

CREATE TABLE IF NOT EXISTS fetch_checkpoint (job VARCHAR, last_symbol VARCHAR, updated_at TIMESTAMP, PRIMARY KEY (job));
