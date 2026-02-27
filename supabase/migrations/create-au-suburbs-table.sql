-- ============================================================
-- Table: au_suburbs
-- Source: Australian Postcodes & Suburbs.xlsx (9861 rows)
-- Purpose: Reference table for Australian suburb/state/postcode lookups.
--          Used as the data source for the suburb multi-select UI picker
--          and for validating suburb+state combinations in agent subscriptions.
-- ============================================================

CREATE TABLE IF NOT EXISTS au_suburbs (
    id          SERIAL PRIMARY KEY,
    suburb      TEXT NOT NULL,
    state       TEXT NOT NULL,
    postcode    TEXT NOT NULL,
    -- Computed canonical key used for lookups and as the value stored
    -- in agent_subscriptions.subscribed_suburbs array
    -- Format: UPPER(suburb)|UPPER(state)  e.g. 'ARMIDALE|NSW'
    suburb_key  TEXT GENERATED ALWAYS AS (
                    upper(trim(suburb)) || '|' || upper(trim(state))
                ) STORED,
    CONSTRAINT uq_au_suburbs_suburb_state UNIQUE (suburb, state)
);

-- Index for fast suburb_key lookups (used in agent subscription queries)
CREATE INDEX IF NOT EXISTS idx_au_suburbs_key   ON au_suburbs (suburb_key);

-- Index for state filtering (used by UI dropdown: select state → list suburbs)
CREATE INDEX IF NOT EXISTS idx_au_suburbs_state ON au_suburbs (upper(state));

-- Index for postcode lookups
CREATE INDEX IF NOT EXISTS idx_au_suburbs_pc    ON au_suburbs (postcode);

COMMENT ON TABLE  au_suburbs               IS 'Reference table of Australian suburbs with state and postcode.';
COMMENT ON COLUMN au_suburbs.suburb_key    IS 'Canonical lookup key: UPPER(suburb)|UPPER(state). Stored in agent_subscriptions.subscribed_suburbs[].';
COMMENT ON COLUMN au_suburbs.suburb        IS 'Suburb name as provided in source data (mixed case preserved).';
COMMENT ON COLUMN au_suburbs.state         IS 'State/territory code: NSW, VIC, QLD, SA, WA, TAS, NT, ACT.';
COMMENT ON COLUMN au_suburbs.postcode      IS 'Australian postcode. Stored as TEXT to preserve leading zeros (e.g. 0800).';
