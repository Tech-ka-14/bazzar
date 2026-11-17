-- 0005_analytics_cache.sql — P7-C (roadmap 7.3): result cache for the
-- /api/v1/analytics/* quant endpoints. Keyed by a SHA-256 of
-- (endpoint, canonical params JSON, data fingerprint) where the fingerprint
-- is the MAX(date) + row count of the underlying close series, so a fresh
-- ingest automatically invalidates stale entries. Owned by migrations (not
-- db_config.json) because it is an ops table, same pattern as 0002/0004.

CREATE TABLE IF NOT EXISTS analytics_cache (
    cache_key VARCHAR NOT NULL,
    endpoint VARCHAR NOT NULL,
    params_json VARCHAR NOT NULL,
    data_asof VARCHAR NOT NULL,
    payload_json VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (cache_key)
);
