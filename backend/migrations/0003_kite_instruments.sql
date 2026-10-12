-- P3: Kite instrument-master fields on the securities table.
-- instrument_token is Kite's numeric id (needed for historical-data calls);
-- lot_size/tick_size come from the instrument dump.

ALTER TABLE securities ADD COLUMN IF NOT EXISTS instrument_token BIGINT;
ALTER TABLE securities ADD COLUMN IF NOT EXISTS lot_size INTEGER;
ALTER TABLE securities ADD COLUMN IF NOT EXISTS tick_size DOUBLE;
