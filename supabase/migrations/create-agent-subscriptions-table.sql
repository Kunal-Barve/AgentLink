-- Table: agent_subscriptions
-- Merged table replacing both:
--   - "Agents Subscribed" Sheet1      (1 row per agent per suburb)
--   - "Featured Agent Controls" Sheet1 (1 row per agent per suburb, commission repeated)
--
-- New structure: 1 row per agent per STATE
--   - subscribed_suburbs: Postgres TEXT[] array of 'SUBURB|STATE|POSTCODE' keys
--     e.g. ['ARMIDALE|NSW|2350', 'ABERFOYLE|NSW|2350', ...]
--   - Commission/marketing columns appear once per row (no duplication across suburbs)
--
-- Lookup query:
--   SELECT * FROM agent_subscriptions
--   WHERE state = 'NSW'
--   AND 'ARMIDALE|NSW|2350' = ANY(subscribed_suburbs);

CREATE TABLE IF NOT EXISTS agent_subscriptions (
    id                      UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Agent identity
    name                    TEXT NOT NULL,
    email                   TEXT,
    phone                   TEXT,

    -- Subscription scope: one row per agent per state
    state                   TEXT NOT NULL,
    subscribed_suburbs      TEXT[] NOT NULL DEFAULT '{}',
    -- Each element is a 'SUBURB|STATE|POSTCODE' key matching au_suburbs.suburb_key
    -- e.g. ARRAY['ARMIDALE|NSW|2350', 'ABERFOYLE|NSW|2350']

    -- Subscription details
    subscription_type       TEXT,            -- 'Featured', 'Featured Plus', etc.
    subscription_date       DATE,
    period                  TEXT,
    agent_status            TEXT,            -- 'Active', 'Cancelled', etc.
    manually_pull_data      TEXT,            -- 'Yes' / 'No'
    ad_group                TEXT,
    mrr                     NUMERIC,

    -- Sales performance (pulled from domain.com.au)
    total_sales             TEXT,
    total_sales_value       TEXT,
    median_sold_price       TEXT,

    -- Branding
    agency                  TEXT,
    agent_photo             TEXT,
    agency_photo            TEXT,

    -- Commission rates (TEXT to preserve range format e.g. '2.70-2.90%')
    comm_less_500k          TEXT,   -- Less than $500k Commission
    comm_500k_1m            TEXT,   -- $500k-$1m Commission
    comm_1m_1_5m            TEXT,   -- $1m-$1.5m Commission
    comm_1_5m_2m            TEXT,   -- $1.5m-$2m Commission
    comm_2m_2_5m            TEXT,   -- $2m-$2.5m Commission
    comm_2_5m_3m            TEXT,   -- $2.5m-$3m Commission
    comm_3m_3_5m            TEXT,   -- $3-$3.5m Commission
    comm_3_5m_4m            TEXT,   -- $3.5m-$4m Commission
    comm_4m_6m              TEXT,   -- $4m-$6m Commission
    comm_6m_8m              TEXT,   -- $6m-$8m Commission
    comm_8m_10m             TEXT,   -- $8m-$10m Commission
    comm_10m_plus           TEXT,   -- $10m+ Commission

    -- Marketing budget ranges (TEXT to preserve range format e.g. '$4,000-$5,000')
    mkt_less_500k           TEXT,   -- Less than $500k Marketing
    mkt_500k_1m             TEXT,   -- $500k-$1m Marketing
    mkt_1m_1_5m             TEXT,   -- $1m-$1.5m Marketing
    mkt_1_5m_2m             TEXT,   -- $1.5m-$2m Marketing
    mkt_2m_2_5m             TEXT,   -- $2m-$2.5m Marketing
    mkt_2_5m_3m             TEXT,   -- $2.5m-$3m Marketing
    mkt_3m_3_5m             TEXT,   -- $3m-$3.5m Marketing
    mkt_3_5m_4m             TEXT,   -- $3.5m-$4m Marketing
    mkt_4m_6m               TEXT,   -- $4m-$6m Marketing
    mkt_6m_8m               TEXT,   -- $6m-$8m Marketing
    mkt_8m_10m              TEXT,   -- $8m-$10m Marketing
    mkt_10m_plus            TEXT,   -- $10m+ Marketing

    -- Timestamps
    created_at              TIMESTAMPTZ DEFAULT now(),
    updated_at              TIMESTAMPTZ DEFAULT now(),

    -- One agent can only have one row per state
    CONSTRAINT uq_agent_subscriptions_name_state UNIQUE (name, state)
);

-- GIN index for fast array containment queries on subscribed_suburbs
-- Powers: WHERE 'ARMIDALE|NSW|2350' = ANY(subscribed_suburbs)
CREATE INDEX IF NOT EXISTS idx_agent_subs_suburbs
    ON agent_subscriptions USING GIN (subscribed_suburbs);

-- Index for state lookups
CREATE INDEX IF NOT EXISTS idx_agent_subs_state
    ON agent_subscriptions (state);

-- Index for agent name lookups
CREATE INDEX IF NOT EXISTS idx_agent_subs_name
    ON agent_subscriptions (name);

-- Index for subscription type filtering
CREATE INDEX IF NOT EXISTS idx_agent_subs_type
    ON agent_subscriptions (subscription_type);

-- Auto-update updated_at on row change
CREATE OR REPLACE FUNCTION update_agent_subscriptions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_agent_subscriptions_updated_at
    BEFORE UPDATE ON agent_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_subscriptions_updated_at();

COMMENT ON TABLE  agent_subscriptions IS 'Merged agent subscription and commission table. One row per agent per state. Replaces Agents Subscribed and Featured Agent Controls sheets.';
COMMENT ON COLUMN agent_subscriptions.subscribed_suburbs IS 'Array of suburb keys this agent covers in this state. Format: SUBURB|STATE|POSTCODE e.g. ARMIDALE|NSW|2350. Use GIN index for ANY() lookups.';
COMMENT ON COLUMN agent_subscriptions.state IS 'State code for this row. An agent with subscriptions in multiple states gets one row per state.';
