-- Table: au_suburbs
-- Source: Australian Postcodes & Suburbs.xlsx (9861 rows)
-- Purpose: Reference table for Australian suburb/state/postcode lookups.
-- Used as the data source for the suburb multi-select UI picker
-- and for validating suburb+state combinations in agent subscriptions.

CREATE TABLE IF NOT EXISTS au_suburbs (
    id          SERIAL PRIMARY KEY,
    suburb      TEXT NOT NULL,
    state       TEXT NOT NULL,
    postcode    TEXT NOT NULL,
    suburb_key  TEXT GENERATED ALWAYS AS (upper(trim(suburb)) || '|' || upper(trim(state)) || '|' || trim(postcode)) STORED,
    CONSTRAINT uq_au_suburbs_suburb_state_postcode UNIQUE (suburb, state, postcode)
);

-- Index for fast suburb_key lookups
CREATE INDEX IF NOT EXISTS idx_au_suburbs_key   ON au_suburbs (suburb_key);

-- Index for state filtering (UI dropdown: select state then list suburbs)
CREATE INDEX IF NOT EXISTS idx_au_suburbs_state ON au_suburbs (state);

-- Index for postcode lookups
CREATE INDEX IF NOT EXISTS idx_au_suburbs_pc    ON au_suburbs (postcode);

COMMENT ON TABLE  au_suburbs            IS 'Reference table of Australian suburbs with state and postcode.';
COMMENT ON COLUMN au_suburbs.suburb_key IS 'Canonical lookup key: UPPER(suburb)|UPPER(state)|postcode. e.g. ARMIDALE|NSW|2350';
COMMENT ON COLUMN au_suburbs.suburb     IS 'Suburb name as provided in source data.';
COMMENT ON COLUMN au_suburbs.state      IS 'State/territory code: NSW, VIC, QLD, SA, WA, TAS, NT, ACT.';
COMMENT ON COLUMN au_suburbs.postcode   IS 'Australian postcode stored as TEXT to preserve leading zeros (e.g. 0800).';
