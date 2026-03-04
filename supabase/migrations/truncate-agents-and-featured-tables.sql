-- Clear agents_subscribed and featured_agent_controls (Sheet1 only)
-- Run in Supabase SQL Editor before re-syncing from xlsx

DELETE FROM agents_subscribed;
DELETE FROM featured_agent_controls;
