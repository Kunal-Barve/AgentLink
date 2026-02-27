-- ============================================================
-- CLEANUP: Remove all duplicate/redundant data from sync tables
-- This will clear all data but keep table structures
-- Run this in Supabase Studio SQL Editor
-- Uses DELETE instead of TRUNCATE for compatibility
-- ============================================================

-- Featured Agent Controls tables
DELETE FROM featured_agent_controls;
DELETE FROM featured_agent_controls_sheet3;

-- Agents Subscribed tables
DELETE FROM agents_subscribed;
DELETE FROM agents_subscribed_costs_charges;
DELETE FROM agents_subscribed_agents_cancelled_subscriptions;
DELETE FROM agents_subscribed_area_key;

-- Copy of Agents Subscribed tables
DELETE FROM copy_of_agents_subscribed_agent_subscribed;

-- Copy of Leads Sent tables (these are named leads_sent in your DB)
DELETE FROM leads_sent;
DELETE FROM leads_sent_advocacy;
DELETE FROM leads_sent_leaderboard;
DELETE FROM leads_sent_agent_report;

-- Also clean any copy_of_leads_sent if they exist
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'copy_of_leads_sent') THEN
        DELETE FROM copy_of_leads_sent;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'copy_of_leads_sent_advocacy') THEN
        DELETE FROM copy_of_leads_sent_advocacy;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'copy_of_leads_sent_leaderboard') THEN
        DELETE FROM copy_of_leads_sent_leaderboard;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'copy_of_leads_sent_agent_report') THEN
        DELETE FROM copy_of_leads_sent_agent_report;
    END IF;
END $$;

-- Verify all tables are now empty
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name AND table_schema = 'public') as columns,
    0 as rows
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
AND (
    table_name LIKE '%subscribed%' 
    OR table_name LIKE '%leads%' 
    OR table_name LIKE '%featured%'
    OR table_name LIKE '%suburb%'
)
ORDER BY table_name;

-- ============================================================
-- After running this, re-sync all sheets using syncAllTabs
-- The new delete-then-insert strategy will keep data clean
-- ============================================================
