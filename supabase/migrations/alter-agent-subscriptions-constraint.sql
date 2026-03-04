-- Alter agent_subscriptions to support NULL state
-- Most agents get state = NULL (one row for all states, same commission rates).
-- Only agents with different commission rates per state get state filled (e.g. Aman Singh).
-- UNIQUE NULLS NOT DISTINCT ensures (name=X, state=NULL) is treated as a unique value
-- preventing duplicate null-state rows for the same agent.

-- Step 1: drop NOT NULL constraint on state
ALTER TABLE agent_subscriptions ALTER COLUMN state DROP NOT NULL;

-- Step 2: replace unique constraint with NULL-aware version
ALTER TABLE agent_subscriptions DROP CONSTRAINT IF EXISTS uq_agent_subscriptions_name_state;
ALTER TABLE agent_subscriptions ADD CONSTRAINT uq_agent_subscriptions_name_state
    UNIQUE NULLS NOT DISTINCT (name, state);
