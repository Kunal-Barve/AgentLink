-- ============================================================
-- Fix agents_subscribed table - has wrong columns
-- DROP and recreate with correct columns from Excel
-- ============================================================

-- DROP old table with wrong columns
DROP TABLE IF EXISTS agents_subscribed CASCADE;

-- Recreate with all 43 columns from Agents Subscribed.xlsx / Sheet1
CREATE TABLE agents_subscribed (
    id BIGSERIAL PRIMARY KEY,
    name TEXT,
    email TEXT,
    phone TEXT,
    state TEXT,
    suburb TEXT,
    subscription_date TEXT,
    period TEXT,
    subscription_type TEXT,
    manully_pull_data TEXT,
    total_sales TEXT,
    total_sales_value TEXT,
    median_sold_price TEXT,
    agency TEXT,
    agent_photo TEXT,
    agency_photo TEXT,
    postcode TEXT,
    ad_group TEXT,
    mrr TEXT,
    agent_status TEXT,
    less_than_500k_commission TEXT,
    "500k_1m_commission" TEXT,
    "1m_1_5m_commission" TEXT,
    "1_5m_2m_commission" TEXT,
    "2m_2_5m_commission" TEXT,
    "2_5m_3m_commission" TEXT,
    "3_3_5m_commission" TEXT,
    "3_5m_4m_commission" TEXT,
    "4m_6m_commission" TEXT,
    "6m_8m_commission" TEXT,
    "8m_10m_commission" TEXT,
    "10m_commission" TEXT,
    less_than_500k_marketing TEXT,
    "500k_1m_marketing" TEXT,
    "1m_1_5m_marketing" TEXT,
    "1_5m_2m_marketing" TEXT,
    "2m_2_5m_marketing" TEXT,
    "2_5m_3m_marketing" TEXT,
    "3m_3_5m_marketing" TEXT,
    "3_5m_4m_marketing" TEXT,
    "4m_6m_marketing" TEXT,
    "6m_8m_marketing" TEXT,
    "8m_10m_marketing" TEXT,
    "10m_marketing" TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
ALTER TABLE agents_subscribed ENABLE ROW LEVEL SECURITY;

-- Verify table created
SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_name = 'agents_subscribed' AND table_schema = 'public') as column_count
FROM information_schema.tables 
WHERE table_name = 'agents_subscribed';

-- ============================================================
-- After running: Restart PostgREST
-- ssh root@72.62.64.72
-- cd ~/supabase-app
-- docker restart supabase-rest
-- ============================================================
