-- ============================================================
-- STEP 1: DROP existing suburb_leads tables (created with basic columns)
-- STEP 2: CREATE tables with full column definitions
-- Run this in Supabase Studio SQL Editor
-- ============================================================

-- DROP existing tables
DROP TABLE IF EXISTS suburb_leads_no_agent CASCADE;
DROP TABLE IF EXISTS suburb_leads_no_agent_nsw CASCADE;
DROP TABLE IF EXISTS suburb_leads_no_agent_qld CASCADE;
DROP TABLE IF EXISTS suburb_leads_no_agent_wa CASCADE;
DROP TABLE IF EXISTS suburb_leads_no_agent_vic CASCADE;
DROP TABLE IF EXISTS suburb_leads_no_agent_sa CASCADE;
DROP TABLE IF EXISTS suburb_leads_no_agent_nt CASCADE;
DROP TABLE IF EXISTS suburb_leads_no_agent_tas CASCADE;
DROP TABLE IF EXISTS suburb_leads_no_agent_act CASCADE;

-- Sheet1 tab
CREATE TABLE suburb_leads_no_agent (
    id BIGSERIAL PRIMARY KEY,
    state TEXT,
    suburb TEXT,
    address TEXT,
    owner_name TEXT,
    owner_email TEXT,
    owner_phone TEXT,
    spoken_to_agent TEXT,
    agent_name TEXT,
    looking_to TEXT,
    estimated_value TEXT,
    date_recieved TEXT,
    agent_name_1 TEXT,
    agent_email TEXT,
    featured_or_plus TEXT,
    property_type TEXT,
    when_are_you_looking_to_sell TEXT,
    commission_discount TEXT,
    agents_agency TEXT,
    error_resubmit TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
ALTER TABLE suburb_leads_no_agent ENABLE ROW LEVEL SECURITY;

-- NSW tab
CREATE TABLE suburb_leads_no_agent_nsw (
    id BIGSERIAL PRIMARY KEY,
    state TEXT,
    suburb TEXT,
    address TEXT,
    owner_name TEXT,
    owner_email TEXT,
    owner_phone TEXT,
    spoken_to_agent TEXT,
    agent_name TEXT,
    looking_to TEXT,
    estimated_value TEXT,
    date_recieved TEXT,
    agent_name_1 TEXT,
    agent_email TEXT,
    featured_or_plus TEXT,
    property_type TEXT,
    when_are_you_looking_to_sell TEXT,
    commission_discount TEXT,
    agents_agency TEXT,
    error_resubmit TEXT,
    column_20 TEXT,
    column_21 TEXT,
    column_22 TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
ALTER TABLE suburb_leads_no_agent_nsw ENABLE ROW LEVEL SECURITY;

-- QLD tab
CREATE TABLE suburb_leads_no_agent_qld (
    id BIGSERIAL PRIMARY KEY,
    state TEXT,
    suburb TEXT,
    address TEXT,
    owner_name TEXT,
    owner_email TEXT,
    owner_phone TEXT,
    spoken_to_agent TEXT,
    agent_name TEXT,
    looking_to TEXT,
    estimated_value TEXT,
    date_recieved TEXT,
    agent_name_1 TEXT,
    agent_email TEXT,
    featured_or_plus TEXT,
    property_type TEXT,
    when_are_you_looking_to_sell TEXT,
    commission_discount TEXT,
    agents_agency TEXT,
    error_resubmit TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
ALTER TABLE suburb_leads_no_agent_qld ENABLE ROW LEVEL SECURITY;

-- WA tab
CREATE TABLE suburb_leads_no_agent_wa (
    id BIGSERIAL PRIMARY KEY,
    state TEXT,
    suburb TEXT,
    address TEXT,
    owner_name TEXT,
    owner_email TEXT,
    owner_phone TEXT,
    spoken_to_agent TEXT,
    agent_name TEXT,
    looking_to TEXT,
    estimated_value TEXT,
    date_recieved TEXT,
    agent_name_1 TEXT,
    agent_email TEXT,
    featured_or_plus TEXT,
    property_type TEXT,
    when_are_you_looking_to_sell TEXT,
    commission_discount TEXT,
    agents_agency TEXT,
    error_resubmit TEXT,
    column_20 TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
ALTER TABLE suburb_leads_no_agent_wa ENABLE ROW LEVEL SECURITY;

-- VIC tab
CREATE TABLE suburb_leads_no_agent_vic (
    id BIGSERIAL PRIMARY KEY,
    state TEXT,
    suburb TEXT,
    address TEXT,
    owner_name TEXT,
    owner_email TEXT,
    owner_phone TEXT,
    spoken_to_agent TEXT,
    agent_name TEXT,
    looking_to TEXT,
    estimated_value TEXT,
    date_recieved TEXT,
    agent_name_1 TEXT,
    agent_email TEXT,
    featured_or_plus TEXT,
    property_type TEXT,
    when_are_you_looking_to_sell TEXT,
    commission_discount TEXT,
    agents_agency TEXT,
    error_resubmit TEXT,
    column_20 TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
ALTER TABLE suburb_leads_no_agent_vic ENABLE ROW LEVEL SECURITY;

-- SA tab
CREATE TABLE suburb_leads_no_agent_sa (
    id BIGSERIAL PRIMARY KEY,
    state TEXT,
    suburb TEXT,
    address TEXT,
    owner_name TEXT,
    owner_email TEXT,
    owner_phone TEXT,
    spoken_to_agent TEXT,
    agent_name TEXT,
    looking_to TEXT,
    estimated_value TEXT,
    date_recieved TEXT,
    agent_name_1 TEXT,
    agent_email TEXT,
    featured_or_plus TEXT,
    property_type TEXT,
    when_are_you_looking_to_sell TEXT,
    commission_discount TEXT,
    agents_agency TEXT,
    error_resubmit TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
ALTER TABLE suburb_leads_no_agent_sa ENABLE ROW LEVEL SECURITY;

-- NT tab
CREATE TABLE suburb_leads_no_agent_nt (
    id BIGSERIAL PRIMARY KEY,
    state TEXT,
    suburb TEXT,
    address TEXT,
    owner_name TEXT,
    owner_email TEXT,
    owner_phone TEXT,
    spoken_to_agent TEXT,
    agent_name TEXT,
    looking_to TEXT,
    estimated_value TEXT,
    date_recieved TEXT,
    agent_name_1 TEXT,
    agent_email TEXT,
    featured_or_plus TEXT,
    property_type TEXT,
    when_are_you_looking_to_sell TEXT,
    commission_discount TEXT,
    agents_agency TEXT,
    error_resubmit TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
ALTER TABLE suburb_leads_no_agent_nt ENABLE ROW LEVEL SECURITY;

-- TAS tab
CREATE TABLE suburb_leads_no_agent_tas (
    id BIGSERIAL PRIMARY KEY,
    state TEXT,
    suburb TEXT,
    address TEXT,
    owner_name TEXT,
    owner_email TEXT,
    owner_phone TEXT,
    spoken_to_agent TEXT,
    agent_name TEXT,
    looking_to TEXT,
    estimated_value TEXT,
    date_recieved TEXT,
    agent_name_1 TEXT,
    agent_email TEXT,
    featured_or_plus TEXT,
    property_type TEXT,
    when_are_you_looking_to_sell TEXT,
    commission_discount TEXT,
    agents_agency TEXT,
    error_resubmit TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
ALTER TABLE suburb_leads_no_agent_tas ENABLE ROW LEVEL SECURITY;

-- ACT tab
CREATE TABLE suburb_leads_no_agent_act (
    id BIGSERIAL PRIMARY KEY,
    state TEXT,
    suburb TEXT,
    address TEXT,
    owner_name TEXT,
    owner_email TEXT,
    owner_phone TEXT,
    spoken_to_agent TEXT,
    agent_name TEXT,
    looking_to TEXT,
    estimated_value TEXT,
    date_recieved TEXT,
    agent_name_1 TEXT,
    agent_email TEXT,
    featured_or_plus TEXT,
    property_type TEXT,
    when_are_you_looking_to_sell TEXT,
    commission_discount TEXT,
    agents_agency TEXT,
    error_resubmit TEXT,
    make_form TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
ALTER TABLE suburb_leads_no_agent_act ENABLE ROW LEVEL SECURITY;

-- Verify tables created
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_name LIKE 'suburb_leads%'
ORDER BY table_name;

-- ============================================================
-- IMPORTANT: Restart PostgREST after running this!
-- ssh root@72.62.64.72
-- cd ~/supabase-app
-- docker restart supabase-rest
-- ============================================================
